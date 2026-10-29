# Optional Snowflake setup

For the new native **Cortex Agent + Cortex Analyst + Cortex Search** flow, complete this base connection/market setup first, then follow [knowledge-first setup](knowledge-first-architecture.md#setup-and-trial-cost). The older `SIGNAL_AI_MODE=snowflake` path below remains a direct AI_COMPLETE adapter; `snowflake_agent` selects the new orchestration.

**Initial build status: local app tested; Snowflake authentication and live model execution not completed.** Account identifiers do not authenticate a programmatic session. The project contains no password, token, account-specific host or private key. Do not paste secrets into a chat or commit them.

The application uses current `AI_COMPLETE` syntax. Model availability, region access, trial entitlements, privileges and billing must be checked in the actual account. The default model name is configurable, not a guarantee of availability. Official references were checked during the build on 29 October 2026.

1. In Snowsight, review and run [setup.sql](../snowflake/setup.sql) with a role allowed to create the dedicated demo database, stage and X-Small warehouse. The script creates no scheduled tasks or Cortex Search services. Review optional resource-monitor statements separately.
2. Install the optional connector in an isolated environment:

   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # macOS/Linux: source .venv/bin/activate
   python -m pip install -r requirements-snowflake.txt
   ```

3. Configure a secure local named connection using Snowflake's supported connector configuration. For example, in your user-level `~/.snowflake/connections.toml`, outside the repository:

   ```toml
   [signal_starts]
   account = "YOUR_ORG-YOUR_ACCOUNT"
   user = "YOUR_USER"
   authenticator = "externalbrowser"
   warehouse = "SIGNAL_DEMO_WH"
   database = "SIGNAL_STARTS_DEMO"
   schema = "PUBLIC"
   role = "YOUR_AUTHORIZED_DEMO_ROLE"
   ```

   `externalbrowser` requires an account identity setup that supports the connector's browser authentication flow. If this trial uses a different flow, configure a supported named connection locally with your administrator; do not assume browser login to Snowsight authenticates Python. Key-pair/OAuth secrets belong in local secure configuration only. The app does not automate credential entry.

4. Set the name in your shell and load the generated data:

   ```powershell
   $env:SNOWFLAKE_CONNECTION_NAME = 'signal_starts'
   python -m app.generate
   python -m scripts.snowflake_load
   ```

   The loader expects setup to have been run. It refuses non-empty destination tables before writing data. It verifies all 11 row counts and the Lumora aggregate reconciliation. It retains staged synthetic files for inspection. A partial failure is not automatically retried; inspect the dedicated demo objects before continuing. No drop/truncate is performed.

5. Run [analysis.sql](../snowflake/analysis.sql) to check the principal business metrics independently. Optional: refresh the dashboard cache from those tables with `python -m scripts.snowflake_sync`. Stop the app before a refresh, then restart. It downloads allowlisted tables once, validates relations and counts, then switches the cache atomically. The UI still queries local SQLite, not Snowflake on every interaction.
6. After confirming the model/region and costs, enable actual AI:

   ```powershell
   $env:SIGNAL_AI_MODE = 'snowflake'
   $env:SNOWFLAKE_MODEL = 'YOUR_AVAILABLE_MODEL'
   $env:SIGNAL_AI_MAX_CALLS = '20'
   python -m app.server
   ```

   Only a successful response changes the answer badge to **Live Snowflake AI**. Configured-but-unverified state is not connection success. Errors show the offline mode explicitly. Live answers contain generated interpretation of the local evidence snapshot, with prior turns; the citation check validates IDs, not factual correctness. Review actual answers before a live AI recording.

## Trial budget

The local app costs no Snowflake credits. An explicit upload/refresh uses the warehouse; Cortex inference incurs its own applicable charges. The default cap is 20 attempted AI calls **per server process**, including failures; restarting resets it. Max output is 650 tokens per call, evidence is bounded and identical prompts cache in memory. These are application limits, not an account spending ceiling.

Use an X-Small warehouse, 60-second auto-suspend, query tags and statement timeouts. A warehouse resource monitor does **not** cap all serverless/AI consumption. Review account budgets and AI usage before enabling calls. The trial's dollar balance is not a reliable conversion to a specific number of AI calls, and no expiry date is assumed. Keep other services suspended; no continuous service is required here.

## Official references

- [AI_COMPLETE single-string syntax and parameters](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-string)
- [Migration from legacy Cortex functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql-migrate-legacy-functions)
- [Python Connector connection and authentication](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect)
- [Resource monitor scope and limitations](https://docs.snowflake.com/en/user-guide/resource-monitors)

No deployment, connected data backend or paid AI execution should be claimed from the presence of these scripts alone.
