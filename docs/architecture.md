# Architecture and decisions

Version 2 adds the [knowledge-first Snowflake architecture](knowledge-first-architecture.md), including the Insights Knowledge Base, validation, native Analyst/Search agent orchestration, counterevidence checks and source snapshots. The original local dashboard and direct AI_COMPLETE adapter described below remain available.

The application starts with a business question, a metric contract and source completeness. It computes evidence deterministically before any model is invited to interpret it.

The Python standard library serves buildless HTML/CSS/JavaScript and JSON APIs on loopback. SQLite is a reproducible local store with indexes for monthly scope queries. It avoids a required paid service or dependency installation for a recruiter trying the project. Snowflake remains an explicit optional integration rather than a simulated live connection.

The generator writes a fresh temporary database, enforces relational constraints, then atomically switches the output. A failed generation preserves the old database. A manifest hashes ordered logical records. No large data files enter Git.

The analytics module performs allowlisted parameterized queries. User text cannot become executable SQL. Performance and target coverage must match the territory universe. Missing delivery status is unverified, never “complete.” Competitor and survey scores fail closed on missing records. Partial months retain visible observed counts and full targets, while attainment and year-on-year rates are withheld.

The offline assistant detects data-derived signals and routes a supported set of natural-language intents. It remembers scope across turns in server memory. A named territory changes the conversational scope; “whole market” resets it. This is deliberately labeled deterministic, not general AI. Unknown intents receive a scope explanation. Expected scenario labels live only in the test/evaluation layer.

The optional AI adapter sends a bounded evidence snapshot (summary, query metadata and up to 12 rows per source), six prior messages, and the current question to Snowflake AI_COMPLETE. The model receives source-data boundaries and instructions to distinguish facts, hypotheses and limitations. It never receives SQL execution privileges from the app. A per-process call cap counts failed attempts, and identical prompts use an in-process cache. Citation IDs must be present and allowlisted before a generated answer is displayed. This check does not prove that a citation supports a claim; live semantic evaluation remains required.

Dashboard source endpoints recompute current scoped evidence. Chat answers instead freeze response-specific source cards under an opaque evidence ID, checked against month and territory; up to 200 snapshots are retained in memory. The viewer shows up to 100 rows and exports the complete stored card. Expired snapshots return an explicit error. Conversation history and snapshots are not persisted across restarts.

Snowflake loader and refresh use only constant table names and generated schema metadata. The loader aborts if any target table already contains rows. It bulk uploads staged CSV files, verifies counts, and reconciles starts. Partial loads require manual inspection; there is intentionally no destructive overwrite/retry mode. The refresh validates a separate SQLite cache before switching. Dashboard interactions query the resulting local cache. This keeps trial warehouse activity bounded and makes the backend distinction explicit.

HTTP boundaries include a body limit, text length validation, same-origin checks, allowlisted paths, no permissive CORS, a restrictive content security policy, and escaped UI content. Sessions are capped at 200 and discarded on restart. This is a local demo, not a hardened multi-user service. It has no authentication, durable audit trail, tenancy, sensitive-data controls, streaming responses or production hosting.

Next engineering steps would be authenticated deployment, stable versioned evidence IDs, a warehouse semantic layer, independent live-AI claim evaluation, managed secrets, explicit model/region entitlement checks, concurrent-session serialization, and real operational validation of proposed hypotheses. None of those are claimed as completed.
