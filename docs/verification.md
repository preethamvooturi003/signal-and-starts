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
| GitHub repository | Published and verified at `preethamvooturi003/signal-and-starts`, application commit `a695718277e68f787bbd66fdc1193ad4a053a328`; local and remote tree hashes match |
| GitHub-hosted CI | [Run 40813977529](https://github.com/preethamvooturi003/signal-and-starts/actions/runs/40813977529) completed successfully for the published application commit |
| Snowflake authentication | Not established during the initial build |
| Snowflake DDL/load/cache refresh | Supplied and locally compiled; not executed against the account |
| Live AI responses | Not executed or semantically evaluated; offline and failure labels verified |

The demo video is silent with burned-in captions and separate SRT captions. It is an edited still-capture walkthrough of the actual app, not continuous screen recording. The GitHub end card uses the verified repository URL. The LinkedIn draft has not been posted.

No real-world cost savings, sales growth, clinical accuracy, deployment, patient outcome or causal effect is claimed.

Publication initially failed because saved command-line credentials were invalid and the integration returned HTTP 403. After the user reconnected GitHub, the authenticated integration published all 43 tracked files. The original local build commits remain on the `local-build` branch; `main` tracks the published GitHub branch. GitHub publication does not authenticate the separate Snowflake integration.
