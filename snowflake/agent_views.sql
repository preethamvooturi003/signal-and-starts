-- Prerequisite: setup.sql + the existing synthetic market loader.
-- These are dedicated demo objects. Review grants before running as an administrator.
USE DATABASE SIGNAL_STARTS_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SIGNAL_DEMO_WH;

CREATE OR REPLACE VIEW ANALYST_MONTHLY AS
WITH months AS (SELECT DISTINCT month FROM monthly_performance),
contacts AS (
 SELECT m.month,h.territory_id,h.hcp_id,COUNT(e.event_id) contacts
 FROM months m CROSS JOIN hcps h
 LEFT JOIN engagement_events e ON e.month=m.month AND e.hcp_id=h.hcp_id
 GROUP BY m.month,h.territory_id,h.hcp_id
), ranked AS (
 SELECT *,ROW_NUMBER() OVER (PARTITION BY month,territory_id ORDER BY contacts DESC,hcp_id) contact_rank
 FROM contacts
), engagement AS (
 SELECT month,territory_id,SUM(contacts) engagements,COUNT(*) hcp_universe,
 COUNT_IF(contacts>0) reached_hcps,SUM(IFF(contact_rank<=25,contacts,0)) top_quarter_contacts
 FROM ranked GROUP BY month,territory_id
), competition AS (
 SELECT month,territory_id,COUNT(DISTINCT product_id) brand_count,
 SUM(observed_contacts) total_contacts,SUM(IFF(product_id='LUM',observed_contacts,0)) own_contacts
 FROM competitor_activity GROUP BY month,territory_id
), survey AS (
 SELECT month,territory_id,COUNT(*) responses,COUNT_IF(score>=9) promoters,COUNT_IF(score<=6) detractors
 FROM surveys GROUP BY month,territory_id
), market AS (
 SELECT month,territory_id,SUM(starts) all_brand_starts FROM patient_aggregates GROUP BY month,territory_id
)
SELECT TO_DATE(p.month||'-01') period_month,p.territory_id,t.name territory_name,'LUM' product_id,
 p.naive_starts,p.incoming_switches,p.naive_starts+p.incoming_switches starts,
 g.naive_target,g.switch_target,g.naive_target+g.switch_target target,TO_DATE(g.set_date) target_set_date,
 p.coverage_days,p.period_days,IFF(p.coverage_days=p.period_days,1,0) coverage_complete,
 e.engagements,e.hcp_universe,e.reached_hcps,e.top_quarter_contacts,
 c.own_contacts,c.total_contacts,
 IFF(c.brand_count=3 AND cs.status='complete',1,0) competitor_complete,
 s.responses,s.promoters,s.detractors,30 survey_invited,
 IFF(s.responses=20 AND ss.status='complete',1,0) survey_complete,
 m.all_brand_starts
FROM monthly_performance p JOIN targets g USING(month,territory_id)
JOIN territories t USING(territory_id) JOIN engagement e USING(month,territory_id)
JOIN market m USING(month,territory_id)
LEFT JOIN competition c USING(month,territory_id) LEFT JOIN survey s USING(month,territory_id)
LEFT JOIN source_status cs ON cs.month=p.month AND cs.territory_id=p.territory_id AND cs.source='competitor_activity'
LEFT JOIN source_status ss ON ss.month=p.month AND ss.territory_id=p.territory_id AND ss.source='surveys';

CREATE SEMANTIC VIEW IF NOT EXISTS COMMERCIAL_ANALYTICS
 TABLES (commercial AS SIGNAL_STARTS_DEMO.PUBLIC.ANALYST_MONTHLY PRIMARY KEY (period_month,territory_id))
 DIMENSIONS (
  commercial.period_month AS period_month COMMENT='First calendar day of reporting month; September 2026 is partial.',
  commercial.territory_id AS territory_id,
  commercial.territory_name AS territory_name,
  commercial.product_id AS product_id,
  commercial.target_set_date AS target_set_date,
  commercial.coverage_complete AS coverage_complete,
  commercial.competitor_complete AS competitor_complete,
  commercial.survey_complete AS survey_complete
 )
 METRICS (
  commercial.new_to_brand_starts AS SUM(starts) COMMENT='Naive plus incoming switches; synthetic aggregate demo categories.',
  commercial.naive_starts AS SUM(naive_starts),
  commercial.incoming_switches AS SUM(incoming_switches),
  commercial.business_target AS SUM(target),
  commercial.naive_target AS SUM(naive_target),
  commercial.switch_target AS SUM(switch_target),
  commercial.start_gap AS SUM(target)-SUM(starts),
  commercial.attainment_pct AS IFF(MIN(coverage_complete)=1,100.0*SUM(starts)/NULLIF(SUM(target),0),NULL),
  commercial.engagements AS SUM(engagements),
  commercial.hcp_reach_pct AS 100.0*SUM(reached_hcps)/NULLIF(SUM(hcp_universe),0)
    COMMENT='For one month only. Across months this is HCP-month reach, not unique-period reach.',
  commercial.top_quarter_contact_pct AS 100.0*SUM(top_quarter_contacts)/NULLIF(SUM(engagements),0)
    COMMENT='Territory-defined top quarters; national pooled quartile must be calculated separately.',
  commercial.all_brand_market_starts AS SUM(all_brand_starts),
  commercial.observed_share_of_voice AS IFF(MIN(competitor_complete)=1,100.0*SUM(own_contacts)/NULLIF(SUM(total_contacts),0),NULL),
  commercial.service_promoter_score AS IFF(MIN(survey_complete)=1,100.0*(SUM(promoters)-SUM(detractors))/NULLIF(SUM(responses),0),NULL),
  commercial.valid_survey_responses AS SUM(responses),
  commercial.survey_invitations AS SUM(survey_invited)
 )
 COMMENT='Fictional Lumora commercial metrics; no clinical or employer data.'
 AI_SQL_GENERATION 'Read only. Use the requested month and territory. Compare year-on-year only for complete periods. Show denominators and missing-source flags. Use one-month reach; never call multi-month HCP-month reach unique reach. Market volatility requires first summing all-brand starts by month across all territories, then calculating STDDEV_POP/AVG over six closed months. Hypotheses in retrieved text are not verified explanations.';

-- Provision explicitly; this application refuses to run native agents as an admin role.
CREATE ROLE IF NOT EXISTS SIGNAL_DEMO_AGENT_ROLE;
GRANT USAGE ON WAREHOUSE SIGNAL_DEMO_WH TO ROLE SIGNAL_DEMO_AGENT_ROLE;
GRANT USAGE ON DATABASE SIGNAL_STARTS_DEMO TO ROLE SIGNAL_DEMO_AGENT_ROLE;
GRANT USAGE ON SCHEMA SIGNAL_STARTS_DEMO.PUBLIC TO ROLE SIGNAL_DEMO_AGENT_ROLE;
GRANT SELECT ON VIEW ANALYST_MONTHLY TO ROLE SIGNAL_DEMO_AGENT_ROLE;
GRANT SELECT ON SEMANTIC VIEW COMMERCIAL_ANALYTICS TO ROLE SIGNAL_DEMO_AGENT_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE SIGNAL_DEMO_AGENT_ROLE;
-- Grant this role to the intended demo user separately. No raw-table writes or ownership are granted.
