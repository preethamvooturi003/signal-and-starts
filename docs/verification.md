# Initial build verification record

Recorded 29 October 2026. This file distinguishes executed local checks from supplied integrations.

| Check | Result |
| --- | --- |
| Standard-library unit and HTTP tests | 10 tests passed |
| Controlled offline scenario evaluation | 10/10 cases; precision 1.0, recall 1.0 within the designed cases |
| Generator reproducibility | Two separate generations had identical table counts and logical-record hashes |
| Data volume | 254,356 physical records; 237,183 engagement event rows; 36 months |
| Relational and metric checks | Foreign-key check, Lumora start reconciliation, frozen targets and partial-date bounds passed |
| JavaScript syntax | `node --check web/app.js` passed |
| Python compilation | `python -m compileall -q app scripts tests` passed |
| Browser dashboard | Actual/target, filters, Nordhaven start mix and investigation launch verified |
| Browser conversation | Nordhaven findings and “What should we investigate next?” response verified |
| Browser evidence | F01 opened three field-note rows with IDs and a CSV link; unverified-anecdote warning visible |
| Responsive layout | Desktop 1440px, default narrow browser and 390px breakpoint inspected; filter status overflow repaired |
| Partial month | September showed 18/30 days with attainment and growth withheld |
| Media | H.264 MP4, 1920×1080, 30 fps, exactly 40 seconds; a sampled frame inspected |
| Secret/account scan | No actual Snowflake account identifiers or credentials in publishable source |
| GitHub repository | Created and verified at `preethamvooturi003/signal-and-starts`; local commit exists; first push blocked by invalid CLI credentials and integration HTTP 403 |
| GitHub-hosted CI | See the repository Actions page for actual remote run status; local success does not imply remote success |
| Snowflake authentication | Not established during the initial build |
| Snowflake DDL/load/cache refresh | Supplied and locally compiled; not executed against the account |
| Live AI responses | Not executed or semantically evaluated; offline and failure labels verified |

The demo video is silent with burned-in captions and separate SRT captions. It is an edited still-capture walkthrough of the actual app, not continuous screen recording. The GitHub end card uses the verified repository URL. The LinkedIn draft has not been posted.

No real-world cost savings, sales growth, clinical accuracy, deployment, patient outcome or causal effect is claimed.
