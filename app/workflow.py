"""Knowledge-first offline investigation, with public execution events rather than model thoughts."""
import math
import re
import statistics
from .analytics import context,evidence,rows
from .knowledge import retrieve,VERSION


def validate_question(db,question,month,territory):
    context(db,month,territory)
    if not isinstance(question,str) or not 1<=len(question.strip())<=1200:
        return 'Enter a commercial analytics question of 1–1200 characters.'
    q=question.lower()
    if re.search(r'\b(drop|truncate|delete|update|insert|grant|revoke)\s+(table|from|into|role|database)\b',q):
        return 'This investigation only reads commercial evidence. Ask about starts, targets, engagement or market dynamics.'
    if any(x in q for x in ['which treatment','prescribe','dosage','patient name','patient-level']):
        return 'This synthetic aggregate demo supports commercial investigation, not individual patient data or treatment decisions.'
    explicit=set(re.findall(r'\b20\d{2}-(?:0[1-9]|1[0-2])\b',question))
    if explicit and month not in explicit:
        return f'The dashboard period is {month}. Select the requested period before investigating it, or include {month} explicitly in a comparison question.'
    return None


def volatility_probe(db,month):
    sql="""SELECT p.month,SUM(a.starts) market_starts,COUNT(DISTINCT p.territory_id) territories
      FROM monthly_performance p JOIN patient_aggregates a USING(month,territory_id)
      WHERE p.month<=? AND p.coverage_days=p.period_days
      GROUP BY p.month HAVING COUNT(DISTINCT p.territory_id)=12 AND COUNT(*)=72
      AND COUNT(DISTINCT a.territory_id||a.product_id||a.entry_category)=72
      ORDER BY p.month DESC LIMIT 6"""
    # The shared join has one performance row per territory-month and six aggregate rows.
    data=rows(db,sql,(month,));values=[r['market_starts'] for r in data]
    periods=sorted(int(r['month'][:4])*12+int(r['month'][5:]) for r in data)
    contiguous=len(periods)==6 and all(b-a==1 for a,b in zip(periods,periods[1:]))
    cv=round(100*statistics.pstdev(values)/statistics.mean(values),2) if contiguous and all(values) else None
    return {'id':'V01','title':'Six closed months · all-brand market variability','tables':['patient_aggregates','monthly_performance'],
      'sql':sql,'parameters':[month],'rows':data,'cv_pct':cv,
      'definition':'Population standard deviation / mean of six monthly all-brand starts × 100. Trend and seasonality are not removed; 15% is a demo threshold, not a pharmaceutical standard.'}


def prepare(db,question,month,territory):
    trace=[{'stage':'validate','message':f'Validated the selected scope and {month} period.'}]
    initial=retrieve(question,month,territory)
    trace.append({'stage':'retrieve','message':f'Retrieved {len(initial)} historical insight chunks before querying current metrics. Offline retrieval uses SQLite FTS5, not Cortex Search.'})
    ev=evidence(db,month,territory)
    trace.append({'stage':'query','message':'Executed parameterized current/prior starts, targets, engagement and source-completeness queries.'})
    probe=volatility_probe(db,month)
    trace.append({'stage':'query','message':'Checked the historical volatility narrative against six closed months of all-brand market starts.'})
    second=retrieve('counterevidence alternatives contradiction '+question,month,territory,limit=2,topics=['counterevidence','target'])
    combined={d['chunk_id']:d for d in initial+second}
    trace.append({'stage':'recheck','message':f'Retrieved {len(second)} alternative/context chunks after the metric checks. Older narratives remain hypotheses.'})
    card={'id':'K01','title':'Insights Knowledge Base · retrieved historical interpretations','tables':['insight_chunks'],
      'rows':list(combined.values()),'sql':'SQLite FTS5 MATCH with product, territory, period and publication-cutoff filters; diversified by topic.',
      'parameters':{'question':question,'month':month,'territory':territory,'version':VERSION,'rounds':2}}
    s=ev['summary'];checks=[]
    for d in initial:
        topic=d['topic'];finding='not established';reason='Requires additional independent evidence.';source='P01'
        if topic=='coverage':
            finding='supported pattern' if (s['top_quartile_contact_pct'] or 0)>65 else 'not supported by this check'
            reason=f"Top-quarter concentration {s['top_quartile_contact_pct']}%; HCP reach {s['reach_pct']}%.";source='E01'
        elif topic=='switch_mix':
            finding='unresolved: comparator unavailable' if s['switch_yoy'] is None else ('supported pattern' if s['switch_yoy'] < -25 else 'not supported by this check')
            reason='Year-on-year comparison withheld for this period.' if s['switch_yoy'] is None else f"Incoming-switch year-on-year change: {s['switch_yoy']}%.";source='M01'
        elif topic=='target':
            finding='unresolved: comparator unavailable' if s['actual_yoy'] is None else ('supported pattern' if (s['target_yoy'] or 0)>25 and s['actual_yoy']>-5 else 'not supported by this check')
            reason='Comparable closed-month actual-start growth is unavailable.' if s['actual_yoy'] is None else f"Target growth {s['target_yoy']}%; actual-start growth {s['actual_yoy']}%.";source='P01'
        elif topic=='process':
            reason='Current field notes remain unverified observations; independent workflow timestamps are absent.';source='F01'
        elif topic=='volatility':
            finding='not supported by this check' if probe['cv_pct'] is not None and probe['cv_pct']<15 else 'unresolved'
            reason=f"Six-month market coefficient of variation: {probe['cv_pct']}%.";source='V01'
        checks.append({'document_id':d['document_id'],'topic':topic,'assessment':finding,'evidence':reason,'source':source,'causality':'not established'})
    ev['sources'] += [card,probe]
    return ev,trace,checks
