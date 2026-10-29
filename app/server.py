"""Local HTTP application. Run: python -m app.server"""
import argparse
import csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlparse
import uuid
from .analytics import connect,dashboard,evidence
from .generate import DEFAULT_DB,generate
from .investigate import investigate

STATIC=Path(__file__).resolve().parents[1]/"web"
SESSIONS={}; LOCK=threading.Lock()
AI=None


class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args):
        # Do not log questions, session IDs, credentials or query strings.
        pass

    def send(self,status,payload,content_type="application/json; charset=utf-8"):
        body=json.dumps(payload).encode() if content_type.startswith("application/json") else payload
        self.send_response(status)
        self.send_header("Content-Type",content_type)
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        url=urlparse(self.path); q=parse_qs(url.query)
        month=q.get("month",["2026-08"])[0]; tid=q.get("territory",["ALL"])[0]
        try:
            if url.path=="/api/health":
                return self.send(200,{"ok":True,"data_backend":"local SQLite","ai_mode":"snowflake_configured_unverified" if AI else "offline","synthetic":True})
            if url.path=="/api/dashboard":
                with connect(self.server.db_path) as db:
                    return self.send(200,dashboard(db,month,tid))
            if url.path=="/api/source":
                with connect(self.server.db_path) as db:
                    cards=evidence(db,month,tid)["sources"]
                    card=next((c for c in cards if c["id"]==q.get("id",[""])[0]),None)
                    if card is None:
                        raise ValueError("Unknown source ID")
                    if q.get("format")==["csv"]:
                        out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=list(card["rows"][0]) if card["rows"] else ["no_rows"])
                        writer.writeheader(); writer.writerows(card["rows"])
                        return self.send(200,out.getvalue().encode(),"text/csv; charset=utf-8")
                    return self.send(200,{**card,"rows":card["rows"][:100],"row_count":len(card["rows"]),"display_limit":100})
            files={"/":"index.html","/index.html":"index.html","/app.js":"app.js","/style.css":"style.css"}
            if url.path not in files:
                return self.send(404,{"error":"Not found"})
            path=STATIC/files[url.path]
            mime={".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".css":"text/css; charset=utf-8"}[path.suffix]
            return self.send(200,path.read_bytes(),mime)
        except ValueError as exc:
            self.send(400,{"error":str(exc)})
        except Exception:
            self.send(500,{"error":"Local data query failed. Check dataset generation."})

    def do_POST(self):
        origin=self.headers.get("Origin")
        if origin and origin!=f"http://{self.headers.get('Host')}":
            return self.send(403,{"error":"Cross-origin request refused"})
        if self.path!="/api/chat":
            return self.send(404,{"error":"Not found"})
        if not self.headers.get("Content-Type","").startswith("application/json"):
            return self.send(415,{"error":"Use application/json"})
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=16000:
                return self.send(413,{"error":"Request exceeds size limit"})
            req=json.loads(self.rfile.read(length))
            question=req.get("question","")
            if not isinstance(question,str) or not question.strip() or len(question)>1200:
                raise ValueError("Enter a question of 1–1200 characters.")
            month=req.get("month","2026-08"); tid=req.get("territory","ALL")
            session_id=req.get("session_id")
            with LOCK:
                session=SESSIONS.get(session_id)
                if session is None or session["month"]!=month or session["initial_territory"]!=tid:
                    session_id=uuid.uuid4().hex
                    if len(SESSIONS)>=200:
                        SESSIONS.pop(next(iter(SESSIONS)))
                    session={"month":month,"initial_territory":tid,"territory":tid,"history":[]}
                    SESSIONS[session_id]=session
                history=list(session["history"])
                effective_tid=session["territory"]
            with connect(self.server.db_path) as db:
                result=investigate(db,question.strip(),month,effective_tid,history,AI)
            with LOCK:
                session["territory"]=result["territory"]
                session["history"]=(history+[{"role":"user","content":question},{"role":"assistant","content":"\n".join(result["paragraphs"])}])[-8:]
            self.send(200,{**result,"session_id":session_id})
        except (ValueError,TypeError,KeyError,json.JSONDecodeError):
            self.send(400,{"error":"Invalid question or scope. Select an available month and territory."})
        except Exception:
            self.send(500,{"error":"Investigation failed. Try again after verifying local data."})


def main():
    global AI
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,default=8501)
    parser.add_argument("--db",type=Path,default=DEFAULT_DB)
    args=parser.parse_args()
    if not args.db.exists():
        print("Generating synthetic market…",flush=True)
        manifest=generate(args.db)
        print(f"Created {manifest['total_records']:,} reproducible records.",flush=True)
    mode=os.getenv("SIGNAL_AI_MODE","offline")
    if mode not in ["offline","snowflake"]:
        raise ValueError("SIGNAL_AI_MODE must be offline or snowflake")
    if mode=="snowflake":
        from .snowflake_ai import SnowflakeAI
        AI=SnowflakeAI()
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    server.db_path=args.db.resolve()
    print(f"Signal & Starts: http://127.0.0.1:{args.port} · Demo / Synthetic data · AI: {mode}",flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__=="__main__":
    main()
