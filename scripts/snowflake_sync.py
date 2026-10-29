"""Refresh an atomic, validated local cache from the loaded Snowflake demo market."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
from app.generate import DEFAULT_DB,SCHEMA,TABLES
from app.analytics import evidence
from app.snowflake_ai import open_connection


def sync(path=DEFAULT_DB):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.syncing')
    if temp.exists():raise RuntimeError('An unfinished sync exists. Inspect before removing it.')
    db=sqlite3.connect(temp);db.row_factory=sqlite3.Row;db.executescript(SCHEMA)
    try:
        with open_connection() as sf,sf.cursor() as cur:
            cur.execute('USE DATABASE SIGNAL_STARTS_DEMO');cur.execute('USE SCHEMA PUBLIC');cur.execute('USE WAREHOUSE SIGNAL_DEMO_WH')
            for table in TABLES:
                cols=[r[1] for r in db.execute(f'PRAGMA table_info({table})')]
                cur.execute(f'SELECT COUNT(*) FROM {table}');expected=cur.fetchone()[0]
                cur.execute(f"SELECT {','.join(cols)} FROM {table} ORDER BY {cols[0]}")
                count=0
                while True:
                    batch=cur.fetchmany(10000)
                    if not batch:break
                    db.executemany(f"INSERT INTO {table} VALUES ({','.join('?' for _ in cols)})",batch);count+=len(batch)
                if not count:raise RuntimeError(f'Empty required table: {table}')
                if count!=expected:raise RuntimeError(f'Count mismatch while caching {table}')
                print(f'{table}: {count:,} rows cached',flush=True)
        if db.execute('PRAGMA foreign_key_check').fetchall():raise RuntimeError('Foreign key validation failed')
        for month, in db.execute('SELECT DISTINCT month FROM monthly_performance'):
            evidence(db,month,'ALL')
        mismatch=db.execute("SELECT COUNT(*) FROM monthly_performance p JOIN (SELECT month,territory_id,SUM(starts) starts FROM patient_aggregates WHERE product_id='LUM' GROUP BY month,territory_id) a USING(month,territory_id) WHERE p.naive_starts+p.incoming_switches<>a.starts").fetchone()[0]
        if mismatch:raise RuntimeError('Start reconciliation failed')
        # Store lineage, not credentials; the original synthetic generator remains the source.
        db.execute('INSERT INTO metadata VALUES (?,?)',('data_origin',json.dumps('Snowflake-validated local cache')))
        db.execute('INSERT INTO metadata VALUES (?,?)',('synthetic',json.dumps(True)))
        db.execute('INSERT INTO metadata VALUES (?,?)',('as_of',json.dumps('2026-09-18')))
        db.commit();db.close();os.replace(temp,path)
        print('Cache switched atomically. Dashboard still queries local SQLite; Snowflake refresh is an explicit action.')
    except Exception:
        db.close()
        raise  # Preserve the failed cache for inspection; never replace the working cache.


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--db',type=Path,default=DEFAULT_DB);args=parser.parse_args();sync(args.db)
