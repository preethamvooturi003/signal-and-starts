"""Reproducible aggregate-only synthetic market. Standard library; no network."""
import argparse
import calendar
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "market.db"
SEED = 73021
TERRITORIES = ["Nordhaven", "Eastmere", "Stonebridge", "Westhaven", "Brookfield", "Ashford",
               "Clearwater", "Fairmont", "Lakeside", "Oakridge", "Riverton", "Southport"]
MONTHS = [f"{2023 + (9 + i) // 12}-{(9 + i) % 12 + 1:02d}" for i in range(36)]
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE products(product_id TEXT PRIMARY KEY, name TEXT NOT NULL, company TEXT NOT NULL, is_focus INTEGER NOT NULL);
CREATE TABLE territories(territory_id TEXT PRIMARY KEY, name TEXT NOT NULL, market TEXT NOT NULL);
CREATE TABLE hcps(hcp_id TEXT PRIMARY KEY, territory_id TEXT REFERENCES territories, specialty TEXT NOT NULL, segment TEXT NOT NULL);
CREATE TABLE engagement_events(event_id TEXT PRIMARY KEY, event_date TEXT NOT NULL, month TEXT NOT NULL, hcp_id TEXT REFERENCES hcps, product_id TEXT REFERENCES products, channel TEXT NOT NULL);
CREATE TABLE targets(month TEXT, territory_id TEXT REFERENCES territories, naive_target INTEGER NOT NULL CHECK(naive_target>=0), switch_target INTEGER NOT NULL CHECK(switch_target>=0), set_date TEXT NOT NULL, PRIMARY KEY(month,territory_id));
CREATE TABLE patient_aggregates(aggregate_id TEXT PRIMARY KEY, month TEXT NOT NULL, territory_id TEXT REFERENCES territories, product_id TEXT REFERENCES products, entry_category TEXT CHECK(entry_category IN ('naive','incoming_switch')), starts INTEGER NOT NULL CHECK(starts>=0));
CREATE TABLE monthly_performance(month TEXT, territory_id TEXT REFERENCES territories, naive_starts INTEGER NOT NULL, incoming_switches INTEGER NOT NULL, coverage_days INTEGER NOT NULL, period_days INTEGER NOT NULL, PRIMARY KEY(month,territory_id));
CREATE TABLE competitor_activity(activity_id TEXT PRIMARY KEY, month TEXT NOT NULL, territory_id TEXT REFERENCES territories, product_id TEXT REFERENCES products, observed_contacts INTEGER NOT NULL CHECK(observed_contacts>=0), available_date TEXT NOT NULL);
CREATE TABLE surveys(response_id TEXT PRIMARY KEY, month TEXT NOT NULL, territory_id TEXT REFERENCES territories, hcp_id TEXT REFERENCES hcps, score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 10), question_version TEXT NOT NULL);
CREATE TABLE field_notes(note_id TEXT PRIMARY KEY, month TEXT NOT NULL, territory_id TEXT REFERENCES territories, hcp_id TEXT REFERENCES hcps, theme TEXT NOT NULL, note TEXT NOT NULL);
CREATE TABLE source_status(month TEXT, territory_id TEXT REFERENCES territories, source TEXT, status TEXT NOT NULL, detail TEXT NOT NULL, PRIMARY KEY(month,territory_id,source));
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX engagement_month_hcp ON engagement_events(month,hcp_id);
CREATE INDEX survey_month_territory ON surveys(month,territory_id);
CREATE INDEX notes_month_territory ON field_notes(month,territory_id);
CREATE INDEX patient_month_territory ON patient_aggregates(month,territory_id);
CREATE INDEX competitor_month_territory ON competitor_activity(month,territory_id);
"""
TABLES = ["products", "territories", "hcps", "engagement_events", "targets", "patient_aggregates",
          "monthly_performance", "competitor_activity", "surveys", "field_notes", "source_status"]


def generate(path=DEFAULT_DB, seed=SEED):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".building")
    if temp.exists():
        raise RuntimeError(f"Unfinished build at {temp}; inspect it before removing it.")
    rng = random.Random(seed)
    db = sqlite3.connect(temp)
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO products VALUES (?,?,?,?)", [
        ("LUM", "Lumora", "Aster Therapeutics (fictional)", 1),
        ("VEL", "Velaris", "Vale Bio (fictional)", 0),
        ("ARC", "Arcelia", "Arc Life (fictional)", 0)])
    for ti, name in enumerate(TERRITORIES):
        tid = f"T{ti+1:02d}"
        db.execute("INSERT INTO territories VALUES (?,?,?)", (tid, name, "Asteria (fictional)"))
        hcps = [f"H{ti*100+j+1:04d}" for j in range(100)]
        db.executemany("INSERT INTO hcps VALUES (?,?,?,?)", [(h, tid, "Oncology", "Priority" if j < 25 else "Core") for j, h in enumerate(hcps)])
        for month in MONTHS:
            year, mon = map(int, month.split("-"))
            days = calendar.monthrange(year, mon)[1]
            covered = 18 if month == "2026-09" else days
            fraction = covered / days
            season = 1 + .07 * math.sin((mon-1) * math.pi / 6)
            growth = 1.05 ** (year - 2024)
            naive_base, switch_base = (180 - ti * 5) * season * growth, (110 - ti * 3) * season * growth
            active = month >= "2026-04"
            n_factor, s_factor, ambition = .98, .98, 1.10
            if active and ti == 0:
                n_factor, s_factor = .92, .35
            elif active and ti == 1:
                n_factor, s_factor = .70, .65
            elif active and ti == 2:
                n_factor, s_factor = 1.02, .38
            if year == 2026 and ti == 3:
                ambition = 1.48
            naive, switch = round(naive_base*n_factor*fraction), round(switch_base*s_factor*fraction)
            db.execute("INSERT INTO targets VALUES (?,?,?,?,?)", (month,tid,round(naive_base*ambition),round(switch_base*ambition),f"{year}-01-01"))
            db.execute("INSERT INTO monthly_performance VALUES (?,?,?,?,?,?)", (month,tid,naive,switch,covered,days))
            for pid in ["LUM","VEL","ARC"]:
                for cat, own in [("naive",naive),("incoming_switch",switch)]:
                    count = own if pid == "LUM" else round((naive_base if cat=="naive" else switch_base)*rng.uniform(.6,.9)*fraction)
                    db.execute("INSERT INTO patient_aggregates VALUES (?,?,?,?,?,?)", (f"PA-{month}-{tid}-{pid}-{cat}",month,tid,pid,cat,count))
            # Events are actual synthetic rows, not inflated by a count multiplier.
            total_events = round((470 + ti * 7) * (1.38 if year==2026 else 1) * fraction)
            events = []
            for j in range(total_events):
                if active and ti == 0:
                    hcp = rng.choice(hcps[:25] if rng.random()<.91 else hcps[25:55])
                else:
                    hcp = rng.choice(hcps)
                events.append((f"EV-{month}-{tid}-{j:04d}",f"{month}-{rng.randint(1,covered):02d}",month,hcp,"LUM",rng.choice(["In-person","Email","Remote","Congress"])))
            db.executemany("INSERT INTO engagement_events VALUES (?,?,?,?,?,?)", events)
            delayed = ti == 5 and month >= "2026-08"
            if not delayed:
                own_contacts = total_events
                for pi,pid in enumerate(["LUM","VEL","ARC"]):
                    contact = own_contacts if pi==0 else round(own_contacts*(1.65 if active and ti in [0,2] else .75)*rng.uniform(.96,1.04))
                    db.execute("INSERT INTO competitor_activity VALUES (?,?,?,?,?,?)", (f"CA-{month}-{tid}-{pid}",month,tid,pid,contact,month+f"-{covered:02d}"))
            db.execute("INSERT INTO source_status VALUES (?,?,?,?,?)",(month,tid,"competitor_activity","delayed" if delayed else "complete","Feed delayed; share of voice unavailable." if delayed else "All three fictional brands represented."))
            db.execute("INSERT INTO source_status VALUES (?,?,?,?,?)",(month,tid,"monthly_performance","partial" if fraction<1 else "complete",f"{covered}/{days} calendar days observed; target remains full month." if fraction<1 else "Closed month."))
            # Thirty invited sampled HCPs; voluntary 20 responses; this is not a census.
            no_survey = ti == 7 and month == "2026-08"
            if not no_survey:
                for j,hcp in enumerate(rng.sample(hcps,20)):
                    score = rng.choice([3,4,5,6,6,7,8,8,9,10] if active and ti in [0,1] else [6,7,8,8,9,9,10])
                    db.execute("INSERT INTO surveys VALUES (?,?,?,?,?,?)",(f"SV-{month}-{tid}-{j:02d}",month,tid,hcp,score,"Likelihood to recommend fictional engagement service, 0-10; v1"))
            db.execute("INSERT INTO source_status VALUES (?,?,?,?,?)",(month,tid,"surveys","missing" if no_survey else "complete","No response file delivered; denominator unknown." if no_survey else "20 valid responses / 30 invited; voluntary sample."))
            for j in range(3):
                if active and ti in [0,1]:
                    theme="process"
                    note=["Several sites reported a fictional authorization checklist delay; verify with an operations audit.","Repeat visits reached familiar HCPs; some sites requested help with a fictional onboarding form.","Field observation: fictional referral handoff is unclear at two sites. Unverified anecdote, not a clinical finding."][j]
                elif active and ti == 2:
                    theme="competition"
                    note="A fictional competitor increased educational events. Field staff perceived fewer incoming switches; validate the feed."
                else:
                    theme="routine"
                    note="Routine fictional engagement summary. No specific process issue recorded; absence of a note is not proof of absence."
                db.execute("INSERT INTO field_notes VALUES (?,?,?,?,?,?)",(f"FN-{month}-{tid}-{j}",month,tid,rng.choice(hcps),theme,note))
    meta = {"seed":seed,"generator_version":"1.0","synthetic":True,"as_of":"2026-09-18","default_month":"2026-08","months":36,"market":"Asteria","invited_per_territory_month":30}
    db.executemany("INSERT INTO metadata VALUES (?,?)",[(k,json.dumps(v)) for k,v in meta.items()])
    db.commit()
    counts={t:db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}
    digest=hashlib.sha256()
    for table in TABLES:
        for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid"):
            digest.update(json.dumps(row,separators=(",",":"),ensure_ascii=True).encode())
    db.close()
    os.replace(temp,path)
    manifest={**meta,"records":counts,"total_records":sum(counts.values()),"content_sha256":digest.hexdigest()}
    path.with_suffix(".manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=DEFAULT_DB)
    parser.add_argument("--seed",type=int,default=SEED)
    args=parser.parse_args()
    print(json.dumps(generate(args.output,args.seed),indent=2))
