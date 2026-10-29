"""Evidence-led conversation. Offline mode is explicitly a deterministic assistant."""
import re
from .analytics import evidence
from .workflow import prepare,validate_question

SOURCE_IDS={"P01","M01","E01","C01","S01","F01","D01","K01","V01","Q01"}


def signals(ev):
    s=ev["summary"]; out=[]
    if s["partial"]:
        out.append("partial_period")
    if s["top_quartile_contact_pct"] and s["top_quartile_contact_pct"]>65:
        out.append("uneven_engagement")
    if s["switch_yoy"] is not None and s["switch_yoy"] < -25:
        out.append("switch_decline")
    if any(r["theme"]=="process" for r in ev["sources"][5]["rows"]):
        out.append("process_hypothesis")
    if s["prior_available"] and s["target_yoy"] is not None and s["target_yoy"]>25 and s["actual_yoy"] is not None and s["actual_yoy"]>-5:
        out.append("target_stretch")
    if s["sov"] is None:
        out.append("competitor_unavailable")
    if s["promoter_score"] is None:
        out.append("survey_unavailable")
    return out


def scope_for(db,question,territory):
    q=question.casefold()
    for tid,name in db.execute("SELECT territory_id,name FROM territories"):
        if name.casefold() in q or re.search(r"\b"+tid.casefold()+r"\b",q):
            return tid
    if any(x in q for x in ["whole market","all territories","national","market overall"]):
        return "ALL"
    return territory


def offline_answer(ev,question):
    s=ev["summary"]; flags=signals(ev); q=question.casefold()
    observations=[]; hypotheses=[]; next_steps=[]; limits=[]
    fmt=lambda n:f"{n:,}"
    if s["partial"]:
        observations.append(f"Only {s['coverage_days']}/{s['period_days']} days are observed. {fmt(s['actual'])} starts cannot be fairly compared with the full-month target of {fmt(s['target'])}. Attainment and year-on-year growth are withheld. [D01] [P01]")
        next_steps.append("Wait for the closed-month delivery before judging performance; compare like-for-like days if a validated daily feed becomes available. [D01]")
    else:
        observations.append(f"Lumora has {fmt(s['actual'])} new-to-brand starts against {fmt(s['target'])} targeted ({s['attainment']}% attainment), a shortfall of {fmt(s['gap'])}. [P01]")
        observations.append(f"Naive starts contribute {fmt(s['naive_gap'])} of the gap; incoming switches contribute {fmt(s['switch_gap'])} ({s['switch_gap_share']}% of the shortfall). [P01]")
        if s["engagement_yoy"] is not None:
            observations.append(f"HCP engagement rose {s['engagement_yoy']}% year on year. Incoming switches changed {s['switch_yoy']}%; naive starts changed {s['naive_yoy']}%. These associations do not establish a cause. [E01] [M01]")
    if "uneven_engagement" in flags:
        observations.append(f"The most contacted quarter of HCPs received {s['top_quartile_contact_pct']}% of contacts. Reach was {s['reached']}/{s['hcps']} HCPs ({s['reach_pct']}%). More contacts did not mean broad coverage. [E01]")
        next_steps.append("Audit HCP reach and repeat-contact concentration before increasing contact volume. Test a broader coverage approach with a predefined comparison group. [E01]")
    if "switch_decline" in flags:
        next_steps.append("Review incoming-switch trends separately from naive starts and validate the fictional referral and onboarding handoff. Do not infer treatment decisions from aggregate commercial data. [M01] [P01]")
    if "process_hypothesis" in flags:
        hypotheses.append("Field notes describe fictional checklist and onboarding delays. A process barrier is a plausible explanation to investigate, but the notes are unverified anecdotes and do not prove why starts fell. [F01]")
        next_steps.append("Ask operations to validate the reported process delays against timestamped, aggregate workflow records. [F01]")
    if "target_stretch" in flags:
        observations.append(f"The target grew {s['target_yoy']}% year on year while observed starts changed {s['actual_yoy']}%. Target stretch merits review alongside demand and capacity assumptions. Targets were frozen at the start of the year. [P01] [M01]")
        next_steps.append("Revisit the beginning-of-year planning assumptions; distinguish target ambition from a deterioration in actual starts. [P01] [M01]")
    if s["sov"] is None:
        limits.append("Competitor delivery is incomplete or delayed in this scope. Share of voice is unavailable; a partial feed must not be presented as market coverage. [D01] [C01]")
    else:
        observations.append(f"Lumora's observed share of voice is {s['sov']}%: Lumora observed contacts / observed contacts across the three fictional brands. This is a proxy for contact activity, not prescriptions or clinical preference. [C01]")
    if s["promoter_score"] is None:
        limits.append("Survey delivery is incomplete. A promoter score for this scope is withheld; do not treat missing responses as neutral scores. [S01] [D01]")
    else:
        observations.append(f"The engagement-service promoter score is {s['promoter_score']} from {s['survey_n']} valid responses / {s['survey_invited']} invited HCPs. It measures a voluntary service survey, not product efficacy. [S01]")
    limits.append("Synthetic aggregate data can prioritize checks, not establish causality. No clinical or real-world business impact is claimed.")
    if not s["prior_available"]:
        limits.append("The same month of the prior year is outside this dataset, so year-on-year comparisons are unavailable. [M01]")
    if not next_steps:
        next_steps.append("Validate source completeness, review the frozen target assumptions, then compare territory-level starts and reach before choosing a test. [P01] [D01] [E01]")
    if any(x in q for x in ["next","recommend","action","should we","do we do"]):
        title="What to investigate next"
        answer=next_steps[:3]+hypotheses+limits
    elif any(x in q for x in ["cause","prove","causal"]):
        title="Evidence supports investigation, not causality"
        answer=observations[:3]+hypotheses+["No. These observational aggregates and field anecdotes do not establish a causal effect. Validate timing, rival explanations and comparable controls before proposing a test. [P01] [F01]"]+limits
    elif any(x in q for x in ["data quality","missing","reliable","limitations","trust","delayed","complete"]):
        title="What the data can support"
        answer=limits+([f"Performance coverage: {s['coverage_days']}/{s['period_days']} days. [D01]"])+observations[-1:]
    elif any(x in q for x in ["survey","promoter","nps"]):
        title="Read the survey with its denominator"
        answer=[o for o in observations if "promoter" in o]+[l for l in limits if "Survey" in l]+["Score = 100 × (promoters scoring 9–10 minus detractors scoring 0–6) / valid responses. Passives score 7–8. Voluntary samples may be biased. [S01]"]
    elif any(x in q for x in ["engagement","reach","contact"]) and not any(x in q for x in ["why","below","despite","target"]):
        title="Volume and coverage tell different stories"
        answer=[o for o in observations if any(x in o for x in ["engagement rose","most contacted"])] + [f"Recorded contacts: {fmt(s['engagements'])}; HCP reach: {s['reach_pct']}%. The top quarter received {s['top_quartile_contact_pct']}% of contacts. [E01]"] + next_steps[:1]+limits[:1]
    elif any(x in q for x in ["competitor","voice"]):
        title="Competitor activity needs a complete feed"
        answer=[o for o in observations if "share of voice" in o]+[l for l in limits if "Competitor" in l]+["Activity and starts may move together for other reasons; this feed alone cannot attribute the start gap to competition. [C01] [P01]"]
    elif any(x in q for x in ["why","investigat","start","gap","switch","target","compare","explain","summar"]):
        title="The gap needs a mix and coverage investigation"
        answer=observations[:4]+hypotheses+([o for o in observations if "target grew" in o])+limits
    else:
        title="A narrower evidence question will help"
        answer=["The offline assistant supports starts, targets, switches, HCP reach, competitor share of voice, surveys, data quality, and next investigation steps. Ask about one of these or enable Snowflake AI for broader language understanding."]+observations[:1]+limits
    return {"title":title,"paragraphs":answer,"observations":observations,"hypotheses":hypotheses,"next_steps":next_steps,"limitations":limits,"signals":flags}


def investigate(db,question,month,territory,history=None,ai=None):
    clarification=validate_question(db,question,month,territory)
    if clarification:
        return {'month':month,'territory':territory,'title':'Clarify the investigation','paragraphs':[clarification],
          'mode':'offline','mode_label':'Question validation','ai_status':'not_requested','signals':[],'sources':[],
          'trace':[{'stage':'validate','message':clarification}],'checks':[],'_source_cards':[]}
    territory=scope_for(db,question,territory)
    if getattr(ai,'native_agent',False):
        try:
            native=ai.run(question,month,territory,history or [])
            return {'month':month,'territory':territory,'title':'Knowledge-led Snowflake investigation',
              'paragraphs':native['paragraphs'],'mode':'snowflake_agent','mode_label':'Live Cortex Agent · Analyst + Search',
              'ai_status':'success','signals':[],'checks':[],
              'trace':native['trace']+[{'stage':'synthesize','message':'Returned interpretation with actual query IDs and historical insight provenance; review factual accuracy.'}],
              'sources':[{'id':c['id'],'title':c['title'],'row_count':len(c['rows'])} for c in native['cards']],
              '_source_cards':native['cards']}
        except Exception as exc:
            print(f'Native Cortex Agent failed ({type(exc).__name__}); using explicitly labeled offline workflow.',flush=True)
            fallback=investigate(db,question,month,territory,history,None)
            fallback.update({'ai_status':'failed','ai_error':'Native Analyst/Search investigation failed or lacked required provenance. Showing offline FTS5 retrieval and local SQL; no live answer is claimed.'})
            return fallback
    ev,trace,checks=prepare(db,question,month,territory)
    result=offline_answer(ev,question)
    knowledge=next(c for c in ev['sources'] if c['id']=='K01')
    probe=next(c for c in ev['sources'] if c['id']=='V01')
    if knowledge['rows']:
        result['paragraphs'].append('Historical manager-style insights were retrieved before the metric checks. They suggest tests for coverage, switching, planning and volatility; their explanations are not accepted as current facts. [K01]')
        if probe['cv_pct'] is not None:
            result['paragraphs'].append(f"The all-brand market coefficient of variation across six closed months is {probe['cv_pct']}%. "+
              ('That weakens the historical volatility narrative under the demo’s 15% heuristic. ' if probe['cv_pct']<15 else 'Variability alone does not establish a cause. ')+
              'Trend and seasonality are not removed. [V01] [K01]')
    else:
        result['paragraphs'].append('No eligible historical insight was available before this reporting cutoff. The answer uses current metric evidence without inventing past context. [K01]')
    result['trace']=trace+[{'stage':'synthesize','message':'Separated observed patterns, historical hypotheses, counterevidence and unresolved questions.'}]
    result['checks']=checks
    result.update({"month":month,"territory":territory,"mode":"offline","mode_label":"Offline evidence assistant · deterministic, no LLM","ai_status":"not_requested"})
    if ai is not None:
        # Errors remain visible; never masquerade a rule response as live AI.
        try:
            answer=ai.complete(question,ev,history or [])
            result.update({"paragraphs":[answer],"title":"Snowflake AI investigation","mode":"snowflake","mode_label":"Live Snowflake AI · generated interpretation","ai_status":"success"})
        except Exception as exc:
            print(f"Snowflake AI failed ({type(exc).__name__}); offline analysis remains labeled. No prompt or credential logged.",flush=True)
            result.update({"ai_status":"failed","ai_error":"Snowflake AI did not return a validated answer. Showing the labeled offline analysis. Check local server logs or the Snowflake setup guide."})
    cited=set(re.findall(r"\[([A-Z]\d{2})\]"," ".join(result["paragraphs"])))
    cited.update(c['source'] for c in checks)
    cited.add('K01')
    result["sources"]=[{"id":c["id"],"title":c["title"],"row_count":len(c["rows"])} for c in ev["sources"] if c["id"] in cited]
    result['_source_cards']=[c for c in ev['sources'] if c['id'] in cited]
    return result
