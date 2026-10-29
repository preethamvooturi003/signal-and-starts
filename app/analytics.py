"""Allowlisted, parameterized, deterministic evidence queries. No model SQL."""
import json
import sqlite3
from .generate import DEFAULT_DB

PERFORMANCE_SQL="""SELECT p.*,t.name, g.naive_target,g.switch_target,g.set_date,
      p.naive_starts+p.incoming_switches actual,g.naive_target+g.switch_target target
      FROM monthly_performance p JOIN targets g USING(month,territory_id)
      JOIN territories t USING(territory_id) WHERE p.month=? AND (?='ALL' OR p.territory_id=?)
      ORDER BY target-actual DESC,t.name"""


def connect(path=DEFAULT_DB):
    db=sqlite3.connect(f"file:{path.as_posix()}?mode=ro",uri=True)
    db.row_factory=sqlite3.Row
    return db


def rows(db,sql,params=()):
    return [dict(r) for r in db.execute(sql,params)]


def pct(now,before):
    return round((now/before-1)*100,1) if before else None


def context(db,month,territory="ALL"):
    months=[r[0] for r in db.execute("SELECT DISTINCT month FROM monthly_performance ORDER BY month")]
    ids={r[0] for r in db.execute("SELECT territory_id FROM territories")}
    if month not in months or territory not in ids|{"ALL"}:
        raise ValueError("Choose an available month and territory.")
    return months


def performance(db,month,territory="ALL"):
    return rows(db,PERFORMANCE_SQL,(month,territory,territory))


def evidence(db,month,territory="ALL"):
    context(db,month,territory)
    params=(month,territory,territory)
    perf=performance(db,month,territory)
    expected=db.execute("SELECT COUNT(*) FROM territories WHERE (?='ALL' OR territory_id=?)",(territory,territory)).fetchone()[0]
    if len(perf)!=expected:
        raise ValueError("Performance or target delivery is incomplete; investigation withheld.")
    prev=f"{int(month[:4])-1}{month[4:]}"
    prior=performance(db,prev,territory)
    sum_key=lambda rr,k:sum(r[k] for r in rr)
    actual=sum_key(perf,"actual"); target=sum_key(perf,"target")
    naive=sum_key(perf,"naive_starts"); switches=sum_key(perf,"incoming_switches")
    nt=sum_key(perf,"naive_target"); st=sum_key(perf,"switch_target")
    partial=any(r["coverage_days"]<r["period_days"] for r in perf)
    engagement_sql="""SELECT h.hcp_id,h.territory_id,COUNT(e.event_id) contacts FROM hcps h
      LEFT JOIN engagement_events e ON h.hcp_id=e.hcp_id AND e.month=?
      WHERE (?='ALL' OR h.territory_id=?) GROUP BY h.hcp_id,h.territory_id ORDER BY contacts DESC,h.hcp_id"""
    er=rows(db,engagement_sql,params)
    ep=rows(db,engagement_sql,(prev,territory,territory))
    count=sum_key(er,"contacts"); prior_events=sum_key(ep,"contacts")
    reached=sum(r["contacts"]>0 for r in er)
    concentration=round(100*sum_key(er[:max(1,len(er)//4)],"contacts")/count,1) if count else None
    competitors=rows(db,"""SELECT a.product_id,p.name,SUM(a.observed_contacts) contacts FROM competitor_activity a
      JOIN products p USING(product_id) WHERE month=? AND (?='ALL' OR territory_id=?) GROUP BY a.product_id,p.name""",params)
    status=rows(db,"SELECT * FROM source_status WHERE month=? AND (?='ALL' OR territory_id=?) ORDER BY source,territory_id",params)
    # Fail closed if a status delivery or an expected brand/survey row disappears.
    for p in perf:
        for source in ["competitor_activity","surveys","monthly_performance"]:
            if not any(s["territory_id"]==p["territory_id"] and s["source"]==source for s in status):
                status.append({"month":month,"territory_id":p["territory_id"],"source":source,"status":"missing","detail":"Source status delivery missing; completeness unverified."})
    if any(s["source"]=="monthly_performance" and s["status"] not in ["complete","partial"] for s in status):
        raise ValueError("Performance completeness is unverified; investigation withheld.")
    comp_ok=not any(s["source"]=="competitor_activity" and s["status"]!="complete" for s in status)
    comp_rows=db.execute("SELECT COUNT(*) FROM competitor_activity WHERE month=? AND (?='ALL' OR territory_id=?)",params).fetchone()[0]
    comp_ok=comp_ok and comp_rows==len(perf)*3 and {c['product_id'] for c in competitors}=={'LUM','VEL','ARC'}
    comp_total=sum_key(competitors,"contacts")
    sov=round(100*sum(c["contacts"] for c in competitors if c["product_id"]=="LUM")/comp_total,1) if comp_ok and comp_total else None
    survey_sql="""SELECT response_id,hcp_id,score,territory_id FROM surveys WHERE month=? AND (?='ALL' OR territory_id=?) ORDER BY response_id"""
    surveys=rows(db,survey_sql,params)
    n=len(surveys); promoters=sum(s["score"]>=9 for s in surveys); detractors=sum(s["score"]<=6 for s in surveys)
    survey_ok=not any(s["source"]=="surveys" and s["status"]!="complete" for s in status)
    survey_ok=survey_ok and n==len(perf)*20
    notes=rows(db,"SELECT * FROM field_notes WHERE month=? AND (?='ALL' OR territory_id=?) ORDER BY CASE theme WHEN 'process' THEN 0 WHEN 'competition' THEN 1 ELSE 2 END,note_id",params)
    summary={"actual":actual,"target":target,"gap":target-actual,"attainment":round(actual/target*100,1) if target and not partial else None,
      "naive":naive,"switches":switches,"naive_target":nt,"switch_target":st,"naive_gap":nt-naive,"switch_gap":st-switches,
      "switch_gap_share":round((st-switches)/(target-actual)*100,1) if target>actual else None,
      "engagements":count,"engagement_yoy":pct(count,prior_events) if not partial else None,"reach_pct":round(reached/len(er)*100,1),
      "hcps":len(er),"reached":reached,"top_quartile_contact_pct":concentration,"sov":sov,"survey_n":n,
      "survey_invited":len(perf)*30 if survey_ok else None,"promoters":promoters,"detractors":detractors,
      "promoter_score":round((promoters-detractors)/n*100,1) if n and survey_ok else None,
      "partial":partial,"coverage_days":perf[0]["coverage_days"],"period_days":perf[0]["period_days"],
      "naive_yoy":pct(naive,sum_key(prior,"naive_starts")) if not partial else None,
      "switch_yoy":pct(switches,sum_key(prior,"incoming_switches")) if not partial else None,
      "actual_yoy":pct(actual,sum_key(prior,"actual")) if not partial else None,
      "target_yoy":pct(target,sum_key(prior,"target")),"prior_actual":sum_key(prior,"actual"),"prior_available":bool(prior)}
    cards=[
      {"id":"P01","title":"Monthly starts & frozen targets","tables":["monthly_performance","targets","territories"],"rows":perf,"sql":PERFORMANCE_SQL,"parameters":list(params)},
      {"id":"M01","title":"Naive vs incoming switches · year-on-year","tables":["monthly_performance","targets","territories"],"rows":prior,"sql":PERFORMANCE_SQL,"parameters":[prev,territory,territory]},
      {"id":"E01","title":"Engagement distribution across all HCPs","tables":["engagement_events","hcps"],"rows":er,"sql":engagement_sql,"parameters":list(params),"comparison":{"prior_month":prev,"prior_contacts":prior_events,"current_contacts":count,"prior_query_parameters":[prev,territory,territory]}},
      {"id":"C01","title":"Observed share of voice","tables":["competitor_activity"],"rows":competitors,"sql":"SELECT product_id, SUM(observed_contacts) FROM competitor_activity WHERE month = :month AND (:territory = 'ALL' OR territory_id = :territory) GROUP BY product_id","parameters":{"month":month,"territory":territory}},
      {"id":"S01","title":"Voluntary HCP service survey","tables":["surveys"],"rows":surveys,"sql":survey_sql,"parameters":list(params)},
      {"id":"F01","title":"Field notes · unverified observations","tables":["field_notes"],"rows":notes,"sql":"SELECT * FROM field_notes WHERE month = :month AND (:territory = 'ALL' OR territory_id = :territory)","parameters":{"month":month,"territory":territory}},
      {"id":"D01","title":"Source delivery & coverage","tables":["source_status"],"rows":status,"sql":"SELECT * FROM source_status WHERE month = :month AND (:territory = 'ALL' OR territory_id = :territory)","parameters":{"month":month,"territory":territory}}]
    return {"month":month,"territory":territory,"summary":summary,"sources":cards}


def dashboard(db,month="2026-08",territory="ALL"):
    months=context(db,month,territory)
    ev=evidence(db,month,territory)
    trend=[]
    for m in [m for m in months if m<=month][-12:]:
        p=performance(db,m,territory)
        trend.append({"month":m,"actual":sum(x["actual"] for x in p),"target":sum(x["target"] for x in p),"partial":any(x["coverage_days"]<x["period_days"] for x in p)})
    return {"month":month,"territory":territory,"summary":ev["summary"],"months":months,"trend":trend,
      "territories":rows(db,"SELECT * FROM territories ORDER BY territory_id"),"ranking":performance(db,month),
      "status":ev["sources"][-1]["rows"],"metadata":{r["key"]:json.loads(r["value"]) for r in rows(db,"SELECT * FROM metadata")}}
