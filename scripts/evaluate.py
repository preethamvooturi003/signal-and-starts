"""Run planted-scenario detection without passing expected labels to the assistant."""
import argparse
import json
from pathlib import Path
from app.analytics import connect
from app.generate import DEFAULT_DB,generate
from app.investigate import investigate

CASES=[
 ('uneven_coverage','2026-08','T01',{'uneven_engagement','switch_decline','process_hypothesis'}),
 ('process_barrier','2026-08','T02',{'switch_decline','process_hypothesis'}),
 ('switch_mix','2026-08','T03',{'switch_decline'}),
 ('target_stretch','2026-08','T04',{'target_stretch'}),
 ('control','2026-08','T05',set()),
 ('delayed_feed','2026-08','T06',{'competitor_unavailable'}),
 ('missing_survey','2026-08','T08',{'survey_unavailable'}),
 ('partial_period','2026-09','T05',{'partial_period'}),
 ('before_change','2026-03','T01',set()),
 ('earliest_period','2023-10','T05',set())]


def evaluate(path=DEFAULT_DB):
    if not Path(path).exists():generate(path)
    results=[];tp=fp=fn=0
    with connect(Path(path)) as db:
        for name,month,tid,expected in CASES:
            reply=investigate(db,'Why are starts below target, and what evidence supports the explanation?',month,tid)
            found=set(reply['signals']);tp+=len(found&expected);fp+=len(found-expected);fn+=len(expected-found)
            results.append({'case':name,'month':month,'territory':tid,'expected':sorted(expected),'detected':sorted(found),'pass':found==expected,
              'citations':[s['id'] for s in reply['sources']],'mode':reply['mode']})
    return {'scope':'Offline deterministic scenario evaluation; not an evaluation of live LLM quality or clinical validity',
      'cases':len(results),'passed':sum(r['pass'] for r in results),'precision':tp/(tp+fp) if tp+fp else 1,
      'recall':tp/(tp+fn) if tp+fn else 1,'false_positives':fp,'false_negatives':fn,'results':results}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--db',type=Path,default=DEFAULT_DB);parser.add_argument('--output',type=Path,default=Path('artifacts/evaluation.json'));args=parser.parse_args()
    report=evaluate(args.db);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed']==report['cases'] else 1)
