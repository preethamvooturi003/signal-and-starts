import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from app.analytics import connect
from app.generate import generate
from app.knowledge import documents,retrieve,eligible,cutoff
from app.investigate import investigate
from app.snowflake_agent import specification,parse_response,SnowflakeAgent
from app.workflow import volatility_probe


def native_response():
    return {'role':'assistant','status':'completed','content':[
      {'type':'thinking','thinking':{'text':'PRIVATE_MODEL_THOUGHT_DO_NOT_DISPLAY'}},
      {'type':'tool_use','tool_use':{'type':'cortex_analyst_text_to_sql','name':'CommercialAnalyst','tool_use_id':'t1','input':{'sql':'SELECT * FROM governed_metrics'}}},
      {'type':'tool_result','tool_result':{'type':'cortex_analyst_text_to_sql','name':'CommercialAnalyst','tool_use_id':'t1','status':'success','content':[{'type':'json','json':{'query_id':'test-query-id','sql':'SELECT starts FROM governed_metrics','result_set':{'data':[[217]]}}}]}},
      {'type':'tool_result','tool_result':{'type':'cortex_search','name':'HistoricalInsights','tool_use_id':'s1','status':'success','content':[{'type':'json','json':{'results':[]}}]}},
      {'type':'text','text':'Historical coverage is a hypothesis [K01]. Executed data show a gap [Q01]. Causality remains unresolved.'}]}


class KnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.path=Path(cls.temp.name)/'market.db';generate(cls.path)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_corpus_identity_and_historical_filters(self):
        self.assertEqual(len(documents()),2592)
        self.assertEqual(len({d['chunk_id'] for d in documents()}),2592)
        selected=retrieve('Why is engagement up but starts below target?','2026-08','T01')
        self.assertEqual(len(selected),6)
        self.assertTrue(all(eligible(d,'2026-08','T01') for d in selected))
        self.assertTrue(all(d['period_month']<'2026-08' and d['published_day']<=20260831 for d in selected))
        self.assertEqual(retrieve('starts','2023-10','T01'),[])

    def test_future_and_wrong_territory_cannot_enter_context(self):
        doc=dict(retrieve('starts','2026-08','T01')[0])
        doc['published_day']=20260901;self.assertFalse(eligible(doc,'2026-08','T01'))
        doc['published_day']=20260801;doc['territory_id']='T02';self.assertFalse(eligible(doc,'2026-08','T01'))
        self.assertEqual(cutoff('2026-09'),20260918)

    def test_execution_order_and_counterevidence(self):
        with connect(self.path) as db:
            result=investigate(db,'Why are starts below target?','2026-08','T01')
        stages=[t['stage'] for t in result['trace']]
        self.assertLess(stages.index('retrieve'),stages.index('query'))
        self.assertGreater(stages.index('recheck'),stages.index('query'))
        checks={c['topic']:c for c in result['checks']}
        self.assertEqual(checks['coverage']['assessment'],'supported pattern')
        self.assertEqual(checks['volatility']['assessment'],'not supported by this check')
        self.assertEqual(checks['process']['assessment'],'not established')
        self.assertTrue(all(c['causality']=='not established' for c in result['checks']))
        self.assertIn('K01',{c['id'] for c in result['sources']})

    def test_market_probe_fails_closed_on_missing_month_rows(self):
        with connect(self.path) as db,sqlite3.connect(':memory:') as memory:
            db.backup(memory);memory.row_factory=sqlite3.Row
            self.assertEqual(volatility_probe(memory,'2026-08')['cv_pct'],4.05)
            memory.execute("DELETE FROM patient_aggregates WHERE month='2026-06' AND aggregate_id='PA-2026-06-T01-VEL-naive'")
            self.assertIsNone(volatility_probe(memory,'2026-08')['cv_pct'])

    def test_validation_runs_before_any_live_call(self):
        class NeverCall:
            native_agent=True
            def run(self,*args):raise AssertionError('An invalid question reached the model')
        with connect(self.path) as db:
            for question in ['DROP TABLE targets','Which treatment should a patient use?','Compare 2025-07 starts']:
                reply=investigate(db,question,'2026-08','T01',ai=NeverCall())
                self.assertEqual(reply['title'],'Clarify the investigation')
                self.assertEqual(reply['ai_status'],'not_requested')

    def test_native_spec_has_scope_filters_and_governed_tools(self):
        request=specification('2026-08','T01',[],'Why the gap?',[])
        self.assertFalse(request['stream'])
        self.assertEqual({t['tool_spec']['type'] for t in request['tools']},{'cortex_search','cortex_analyst_text_to_sql'})
        resources=request['tool_resources'];self.assertIn('semantic_view',resources['CommercialAnalyst'])
        filters=json.dumps(resources['HistoricalInsights']['filter'])
        self.assertIn('20260831',filters);self.assertIn('202608',filters);self.assertIn('T01',filters)

    def test_native_provenance_and_private_thought_filter(self):
        result=parse_response(native_response(),'2026-08','T01',[])
        self.assertNotIn('PRIVATE_MODEL_THOUGHT',json.dumps(result))
        self.assertEqual(result['cards'][1]['rows'][0]['query_id'],'test-query-id')
        broken=native_response();broken['warnings']=[{'code':'tool_unavailable'}]
        with self.assertRaises(ValueError):parse_response(broken,'2026-08','T01',[])
        missing_recheck=native_response();missing_recheck['content']=[b for b in missing_recheck['content'] if b.get('tool_result',{}).get('name')!='HistoricalInsights']
        with self.assertRaises(ValueError):parse_response(missing_recheck,'2026-08','T01',[])
        with self.assertRaises(ValueError):parse_response({'content':[{'type':'text','text':'Sounds plausible [K01] [Q01]'}]},'2026-08','T01',[])

    def test_native_calls_search_before_agent_and_enforces_run_budget(self):
        class Cursor:
            def __init__(self):self.calls=[]
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def execute(self,sql,params=None):self.calls.append((sql,params))
            def fetchone(self):return (json.dumps({'results':[]}) if 'SEARCH_PREVIEW' in self.calls[-1][0] else json.dumps(native_response()),)
        class Connection:
            def __init__(self):self.cur=Cursor()
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def cursor(self):return self.cur
        connection=Connection()
        with patch('app.snowflake_agent.open_connection',return_value=connection):
            agent=SnowflakeAgent();agent.limit=1;agent.run('Why the gap?','2026-08','T01',[])
            self.assertEqual(connection.cur.calls[0][0],'USE ROLE SIGNAL_DEMO_AGENT_ROLE')
            self.assertIn('SEARCH_PREVIEW',connection.cur.calls[1][0]);self.assertIn('AGENT_RUN',connection.cur.calls[2][0])
            with self.assertRaises(RuntimeError):agent.run('Another question','2026-08','T01',[])

    def test_failed_native_call_is_explicitly_offline(self):
        class Broken:
            native_agent=True
            def run(self,*args):raise RuntimeError('unavailable')
        with connect(self.path) as db:reply=investigate(db,'Why the gap?','2026-08','T01',ai=Broken())
        self.assertEqual(reply['mode'],'offline');self.assertEqual(reply['ai_status'],'failed')
        self.assertIn('no live answer',reply['ai_error'])
