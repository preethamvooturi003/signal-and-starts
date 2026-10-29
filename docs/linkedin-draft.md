# LinkedIn draft — review before posting

More HCP engagement. New-to-brand starts still below plan. What should a business analyst investigate next?

I built **Signal & Starts**, an independent pharmaceutical commercial analytics portfolio, to explore that question using a completely fictional market.

The project combines 36 months of reproducible synthetic data, a dashboard, and a source-linked investigation workflow. The goal is to move from “we missed target” to a question the business can actually validate.

In the Nordhaven demo, engagement rises 38.1%, while starts reach 217 against a target of 340. Incoming switches account for 71.5% of the arithmetic shortfall, and 89.8% of contacts go to the most-contacted quarter of HCPs. Field notes suggest a process issue to validate; they do not prove causality.

My contribution spans the business question, metric definitions, relational data model, Python/SQL analytics, dashboard, investigation logic, and evaluation. I also built a Snowflake loading and validation path with an optional Cortex AI integration.

The local version uses an explicitly labeled deterministic evidence assistant. Live Snowflake AI is an optional integration requiring account authentication; I am not presenting offline responses as a language model. Ten controlled scenario checks pass, including missing data and negative controls. That is a test result on synthetic cases, not a claim of real business impact.

This is the direction I’m interested in as an AI-focused business analyst: clear business framing, trustworthy metrics, and AI interactions that help people ask better questions.

Demo and source: https://github.com/preethamvooturi003/signal-and-starts

**Demo · Synthetic data. No real patient or employer data. No clinical recommendations.**

#BusinessAnalysis #Analytics #Snowflake #AI #Python #SQL #PortfolioProject
