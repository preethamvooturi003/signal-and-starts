"""Upload local synthetic tables to dedicated Snowflake objects; no secrets in CLI flags."""
import argparse
import csv
from pathlib import Path
import tempfile
import uuid
from app.analytics import connect
from app.generate import DEFAULT_DB,TABLES
from app.snowflake_ai import open_connection


def load(path=DEFAULT_DB):
    # Requires setup.sql, secure local connection config, and an empty target dataset.
    with connect(path) as db,open_connection() as sf,tempfile.TemporaryDirectory(prefix='signal-starts-') as folder:
        with sf.cursor() as cur:
            cur.execute('USE DATABASE SIGNAL_STARTS_DEMO');cur.execute('USE SCHEMA PUBLIC');cur.execute('USE WAREHOUSE SIGNAL_DEMO_WH')
            # Abort before loading anything if any destination table already has data.
            cur.execute('SHOW TABLES IN SCHEMA SIGNAL_STARTS_DEMO.PUBLIC')
            existing={r[1].upper() for r in cur.fetchall()}
            for table in TABLES:
                if table.upper() in existing:
                    cur.execute(f'SELECT COUNT(*) FROM {table}')
                    if cur.fetchone()[0]:
                        raise RuntimeError('Destination already contains data. Use a fresh demo database or review the existing load; no replacement is automatic.')
            prefix='run_'+uuid.uuid4().hex
            results={}
            for table in TABLES:
                cols=db.execute(f'PRAGMA table_info({table})').fetchall()
                definitions=','.join(f'{c[1]} '+('NUMBER(38,0)' if c[2]=='INTEGER' else 'VARCHAR') for c in cols)
                cur.execute(f'CREATE TABLE IF NOT EXISTS {table} ({definitions})')
                file=Path(folder)/(table+'.csv')
                with file.open('w',newline='',encoding='utf-8') as out:
                    writer=csv.writer(out);writer.writerow([c[1] for c in cols]);writer.writerows(db.execute(f'SELECT * FROM {table} ORDER BY rowid'))
                local=file.as_posix().replace("'","''")
                cur.execute(f"PUT 'file://{local}' @SIGNAL_DEMO_STAGE/{prefix}/ AUTO_COMPRESS=TRUE OVERWRITE=FALSE")
                cur.execute(f"COPY INTO {table} FROM @SIGNAL_DEMO_STAGE/{prefix}/{table}.csv.gz ON_ERROR=ABORT_STATEMENT")
                cur.execute(f'SELECT COUNT(*) FROM {table}');actual=cur.fetchone()[0]
                expected=db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                if actual!=expected:raise RuntimeError(f'Count mismatch for {table}; stop and inspect before any retry.')
                results[table]=actual
                print(f'{table}: {actual:,} verified rows',flush=True)
            cur.execute("SELECT COUNT(*) FROM monthly_performance p JOIN (SELECT month,territory_id,SUM(starts) starts FROM patient_aggregates WHERE product_id='LUM' GROUP BY month,territory_id) a USING(month,territory_id) WHERE p.naive_starts+p.incoming_switches<>a.starts")
            if cur.fetchone()[0]:raise RuntimeError('Aggregate reconciliation failed')
            print('All counts and start aggregates reconciled. Staged synthetic files are retained for inspection.')
            return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--db',type=Path,default=DEFAULT_DB);args=parser.parse_args();load(args.db)
