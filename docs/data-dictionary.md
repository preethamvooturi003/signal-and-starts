# Synthetic data dictionary

The SQLite database is generated locally, not committed. All HCP identifiers are invented. There are no patient IDs, names, addresses, birth dates or free text from real people.

| Table | Grain | Rows, default seed | Key and relations |
| --- | --- | ---: | --- |
| products | Fictional brand | 3 | product_id; focus flag |
| territories | Fictional commercial territory | 12 | territory_id; one fictional market |
| hcps | Fictional HCP | 1,200 | hcp_id → territory_id; segment, specialty |
| engagement_events | Lumora contact event | 237,183 | event_id → hcp_id, product_id; date, month, channel |
| targets | Month × territory | 432 | month + territory_id; naive/switch targets, frozen set_date |
| patient_aggregates | Month × territory × brand × entry category | 2,592 | aggregate_id; starts; no patient-level data |
| monthly_performance | Month × territory, Lumora | 432 | naive_starts, incoming_switches, coverage_days, period_days |
| competitor_activity | Delivered month × territory × brand | 1,290 | activity_id; observed_contacts, available_date; six expected rows deliberately absent |
| surveys | Valid voluntary response | 8,620 | response_id → hcp_id, territory_id; month, 0–10 score, question_version |
| field_notes | Fictional field observation | 1,296 | note_id → hcp_id, territory_id; month, theme, note |
| source_status | Month × territory × source | 1,296 | completeness and delivery explanation for performance, competitors and surveys |

Total: **254,356 domain records**, excluding the small metadata table. SQLite foreign keys protect generated relations. The independent reconciliation compares patient_aggregates for Lumora with monthly_performance at the shared grain. Surveys and field notes reference HCPs in the same territory. Engagement event month and date agree.

The manifest records the seed, row counts and a SHA-256 digest of ordered table content. It hashes serialized records, not database file bytes, so file layout does not affect reproducibility. The fixed reference digest is `f1a2f3b96d351e1fd0ba3a00b533923dc524571839c1cca1073480675e2c4e36`.

SQL evidence uses current scope and month, plus the same month in the previous year when available. Source IDs are scoped request identifiers, not globally unique records: P01 performance/target; M01 prior-period performance/target; E01 engagement distribution; C01 competitor activity; S01 survey responses; F01 field notes; D01 source delivery. Raw source record IDs remain in downloads.
