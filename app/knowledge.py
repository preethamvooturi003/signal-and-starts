"""Versioned synthetic manager-style insights; lexical retrieval is the offline substitute."""
import calendar
from datetime import date,timedelta
from functools import lru_cache
import json
from pathlib import Path
import re
import sqlite3
from .generate import MONTHS,TERRITORIES

VERSION='insights-v1'
TOPICS={
 'coverage':('Repeated contacts can hide a reach gap','A previous review discussed how rising contact volume can remain concentrated among familiar HCPs. Broad coverage and frequency should be checked separately. This historical interpretation does not establish the reason for a later shortfall.','Compare unique HCP reach and the share of contacts going to the most-contacted quarter.','A stable broad reach would contradict a coverage explanation.'),
 'process':('A reported process barrier needs independent validation','An insights manager recorded a hypothesis about fictional onboarding and referral handoff friction. Field observations were incomplete and no workflow timestamps were available. This is an unverified historical interpretation.','Check current field notes and seek independent aggregate workflow timestamps.','Current notes may be absent or disagree; lack of notes does not prove no barrier.'),
 'switch_mix':('Start mix can change beneath the overall trend','An earlier brand review proposed examining incoming switches separately from naive starts when overall starts miss plan. A change in category mix may account for an arithmetic gap without establishing its cause.','Compare naive and incoming-switch starts against target and the same month last year.','If both categories grow similarly, a switch-specific explanation is unsupported.'),
 'target':('A shortfall can reflect planning ambition','A prior planning review noted that a stretched beginning-of-year target can coexist with growing actual starts. Validate the frozen planning assumptions before interpreting every gap as reduced demand.','Compare target growth with actual-start growth and check the target set date.','Declining actual starts would require an explanation beyond target ambition.'),
 'volatility':('Volatile market narratives require a time series','An earlier insights review described the fictional market as volatile. That description is a hypothesis to test with a complete time series, not evidence that volatility explains the current gap.','Calculate the coefficient of variation of market-wide starts over six closed months and inspect brand and territory contributions.','A low six-month coefficient of variation would weaken this narrative; seasonality and trend can also affect it.'),
 'counterevidence':('Do not carry an old explanation into a new month','A later review challenged automatic reuse of old territory explanations. Historical notes may describe a different period or a different population. Look deliberately for evidence that contradicts the first explanation.','Recheck dates, geography, product, coverage and an alternative hypothesis.','A relevant historical insight can still be wrong for the selected period.')}


@lru_cache(maxsize=1)
def documents():
    """2,592 short, single-chunk documents, transparent templates rather than real reports."""
    result=[]
    for month in MONTHS:
        y,m=map(int,month.split('-'));end=date(y,m,calendar.monthrange(y,m)[1]);published=end+timedelta(days=5)
        for i,name in enumerate(TERRITORIES):
            for topic,(title,body,check,opposing) in TOPICS.items():
                tid=f'T{i+1:02d}';doc=f'IKB-{month}-{tid}-{topic}-v1'
                result.append({'chunk_id':doc+'-c01','document_id':doc,'title':f'{name} | {month} | {title}',
                  'content':f'SYNTHETIC MANAGER-STYLE INSIGHT. Period: {month}. Territory: {name}. Brand: Lumora. {body} Suggested validation: {check} Counter-check: {opposing}',
                  'period_month':month,'period_key':int(month.replace('-','')),'published_day':int(published.strftime('%Y%m%d')),
                  'territory_id':tid,'product_id':'LUM','topic':topic,'author_role':'Fictional Insights Manager',
                  'evidence_status':'historical_hypothesis_unverified','version':VERSION,'validation_question':check,'counter_check':opposing})
    return tuple(result)


def cutoff(month):
    y,m=map(int,month.split('-'));return min(int(date(y,m,calendar.monthrange(y,m)[1]).strftime('%Y%m%d')),20260918)


def eligible(doc,month,territory):
    return (doc.get('product_id')=='LUM' and doc.get('period_key',999999)<int(month.replace('-',''))
      and doc.get('published_day',99999999)<=cutoff(month)
      and (territory=='ALL' or doc.get('territory_id') in [territory,'ALL']))


@lru_cache(maxsize=1)
def _index():
    # A cached in-memory FTS5 index is read under a lock by retrieve().
    db=sqlite3.connect(':memory:',check_same_thread=False)
    db.execute('CREATE VIRTUAL TABLE insights_fts USING fts5(title,content,topic)')
    db.executemany('INSERT INTO insights_fts(rowid,title,content,topic) VALUES (?,?,?,?)',[(i+1,d['title'],d['content'],d['topic']) for i,d in enumerate(documents())])
    return db


import threading
_LOCK=threading.Lock()


def retrieve(question,month,territory,limit=6,topics=None):
    tokens=set(re.findall(r'[a-z]{3,}',question.lower()))
    tokens|={'starts','target','engagement','coverage','switch','process','volatility','counterevidence'}
    if topics:tokens|=set(topics)
    match=' OR '.join('"'+w+'"' for w in sorted(tokens)[:45])
    with _LOCK:
        hits=_index().execute('SELECT rowid,bm25(insights_fts) FROM insights_fts WHERE insights_fts MATCH ?',(match,)).fetchall()
    candidates=[]
    for rowid,score in hits:
        d=documents()[rowid-1]
        if eligible(d,month,territory) and (not topics or d['topic'] in topics):
            candidates.append((score,d))
    # Diversify by topic before taking another period of the same hypothesis.
    candidates.sort(key=lambda x:(x[0],-x[1]['published_day'],x[1]['chunk_id']))
    chosen=[];seen=set()
    for _,d in candidates:
        if d['topic'] not in seen:
            chosen.append(dict(d));seen.add(d['topic'])
        if len(chosen)>=limit:break
    return chosen


def export(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(json.dumps(d,ensure_ascii=True) for d in documents())+'\n',encoding='utf-8')
    return len(documents())
