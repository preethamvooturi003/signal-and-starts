"""Export the reproducible Insights Knowledge Base; load to Snowflake only with --load."""
import argparse
from pathlib import Path
from app.knowledge import documents,export
from app.snowflake_ai import open_connection

COLS=['chunk_id','document_id','title','content','period_month','period_key','published_day','territory_id','product_id','topic','author_role','evidence_status','version']


def load():
    with open_connection() as conn,conn.cursor() as cur:
        cur.execute('USE DATABASE SIGNAL_STARTS_DEMO');cur.execute('USE SCHEMA PUBLIC')
        definitions=','.join(c+' '+('NUMBER(8,0)' if c in ['period_key','published_day'] else 'VARCHAR') for c in COLS)
        cur.execute(f'CREATE TABLE IF NOT EXISTS INSIGHT_CHUNKS ({definitions},PRIMARY KEY(CHUNK_ID))')
        cur.execute('SELECT COUNT(*) FROM INSIGHT_CHUNKS')
        if cur.fetchone()[0]:raise RuntimeError('Knowledge table is not empty. Inspect before loading; no overwrite is automatic.')
        data=[tuple(d[c] for c in COLS) for d in documents()]
        cur.executemany(f"INSERT INTO INSIGHT_CHUNKS ({','.join(COLS)}) VALUES ({','.join('%s' for _ in COLS)})",data)
        cur.execute('SELECT COUNT(*),COUNT(DISTINCT CHUNK_ID) FROM INSIGHT_CHUNKS')
        count,distinct=cur.fetchone()
        if count!=len(data) or distinct!=len(data):raise RuntimeError('Knowledge count/identity validation failed')
        print(f'Verified {count:,} synthetic insight chunks. Search service creation remains an explicit separate step.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=Path('data/insights.jsonl'));parser.add_argument('--load',action='store_true');args=parser.parse_args()
    print(f'Exported {export(args.output):,} synthetic historical documents to {args.output}')
    if args.load:load()
