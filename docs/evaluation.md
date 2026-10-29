# Evaluation: what was actually tested

Version 2 adds nine knowledge/agent tests, for **19 automated test methods** in total. They cover historical publication/scope filters, no future-knowledge leakage, knowledge-first ordering, a contradicted volatility narrative, missing aggregate data, question gating, native request/tool contracts, mandatory post-query Search rechecks, actual query provenance, hidden model-thought filtering, attempted-run limits and explicit offline failure behavior. Native calls are mocked contract tests; they do not verify authentication, actual Snowflake provisioning or live model quality. The HTTP test also verifies frozen K01 source snapshots and rejects a mismatched territory.

Run `python -m unittest discover -s tests -v` and `python -m scripts.evaluate` from the repository root. The evaluator creates data if needed and writes `artifacts/evaluation.json`. A versioned initial snapshot is in [evaluation-results.json](evaluation-results.json).

Ten finite scenario cases test exact sets of detected signals. The runtime investigation receives only evidence and the question. Expected labels stay in the evaluator and are not passed to the assistant. The generator's planted assumptions are discoverable source code; this is a transparent controlled benchmark, not a concealed real-world holdout.

| Case | Expected data-derived finding |
| --- | --- |
| Nordhaven, Aug 2026 | Uneven engagement, switch decline, process hypothesis |
| Eastmere, Aug 2026 | Switch decline, process hypothesis |
| Stonebridge, Aug 2026 | Switch decline without uneven-coverage claim |
| Westhaven, Aug 2026 | Target stretch while actual starts grow |
| Brookfield, Aug 2026 | Negative control: no planted signal |
| Ashford, Aug 2026 | Competitor data unavailable |
| Fairmont, Aug 2026 | Survey data unavailable |
| Brookfield, Sep 2026 | Partial-period warning |
| Nordhaven, Mar 2026 | Pre-change negative control |
| Brookfield, Oct 2023 | Earliest period; no fabricated year-on-year metric |

The recorded deterministic evaluation passes **10/10 cases**, with precision/recall 1.0 and zero false-positive/false-negative signal labels within these cases. Those values characterize this designed test set only.

Separate automated tests cover reproducible logical-record hashes, actual row counts, foreign keys, patient-aggregate/start reconciliation, frozen targets, event coverage dates, reference business numbers, survey denominators, source deletions, partial-period withholding, valid citations, causal-question handling, scope persistence, invalid/injected input, failed-live-mode labeling, CSV export and HTTP origin/path boundaries. There are 10 test methods in the initial recorded run.

Browser checks cover desktop/narrow layouts, investigation launch, follow-up, citation drilldown, metric guide and partial period. The UI screenshots show the actual offline app.

**Not evaluated:** live LLM numerical accuracy, semantic citation support, prompt-injection resistance of a real model, arbitrary paraphrases, multi-turn accuracy beyond the supported routing rules, medical validity, clinical outcomes or real commercial impact. Mocked live failures test labels; they do not verify Snowflake authentication or SQL execution. An independent labeled live-answer set and human review would be needed before claiming live-AI quality.
