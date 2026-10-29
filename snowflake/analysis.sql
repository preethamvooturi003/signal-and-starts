-- Queries for independent reconciliation of local results after loading.
USE WAREHOUSE SIGNAL_DEMO_WH;
USE DATABASE SIGNAL_STARTS_DEMO;
USE SCHEMA PUBLIC;
ALTER SESSION SET QUERY_TAG='signal_starts_manual_validation';

-- Frozen target and source reconciliation: expected Nordhaven Aug 2026 = 217 / 340.
SELECT p.month,p.territory_id,p.naive_starts+p.incoming_switches AS actual,
 t.naive_target+t.switch_target AS target,
 t.naive_target+t.switch_target-p.naive_starts-p.incoming_switches AS gap,
 p.coverage_days,p.period_days,t.set_date
FROM monthly_performance p JOIN targets t USING(month,territory_id)
WHERE p.month='2026-08' ORDER BY gap DESC;

-- Survey score always includes denominator and invitation assumption.
SELECT month,territory_id,COUNT(*) valid_responses,30 AS invited,
 100.0*(COUNT_IF(score>=9)-COUNT_IF(score<=6))/NULLIF(COUNT(*),0) service_promoter_score
FROM surveys WHERE month='2026-08' GROUP BY month,territory_id;

-- Observed share of voice is withheld for missing/delayed deliveries.
SELECT a.month,a.territory_id,
 CASE WHEN COUNT(DISTINCT a.product_id)=3 AND MAX(IFF(s.status='complete',0,1))=0
 THEN 100.0*SUM(IFF(a.product_id='LUM',a.observed_contacts,0))/NULLIF(SUM(a.observed_contacts),0)
 END AS observed_sov_pct
FROM competitor_activity a JOIN source_status s
 ON a.month=s.month AND a.territory_id=s.territory_id AND s.source='competitor_activity'
GROUP BY a.month,a.territory_id;

-- Cost-free connection check; run an AI call only after reviewing AI billing and model availability.
SELECT CURRENT_ACCOUNT(),CURRENT_ROLE(),CURRENT_WAREHOUSE();
-- SELECT AI_COMPLETE(model => '<ACCOUNT_AVAILABLE_MODEL>', prompt => 'Reply with: Synthetic demo connected.',
--   model_parameters => OBJECT_CONSTRUCT('temperature',0,'max_tokens',20));
