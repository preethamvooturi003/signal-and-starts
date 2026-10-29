# Metric contract and documented assumptions

All definitions describe a fictional commercial analytics demo. They are not clinical definitions, treatment guidance or representations of an employer's systems.

| Metric | Definition and denominator | Missing/partial behavior |
| --- | --- | --- |
| Naive starts | Aggregate fictional category starts with no previous fictional category treatment; mutually exclusive with incoming switches within a territory-month | Provisional for 18-day September; no individual longitudinal model |
| Incoming switches | Aggregate fictional starts after another fictional brand | No patient journey or switching appropriateness inferred |
| New-to-brand starts | Naive + incoming switches for Lumora | Missing performance or target territory blocks the calculation |
| Gap | Full-month target − observed starts | September gap is provisional; never a like-for-like performance judgment |
| Attainment | 100 × actual starts / full-month target | Withheld for partial period |
| Growth | 100 × (current / same calendar month previous year − 1) | Withheld for partial periods or unavailable/zero prior comparator |
| Engagement | Number of Lumora contact events, all four channels equally weighted | Counts are activity; no quality, prescribing or causal claim |
| HCP reach | Unique contacted HCPs / all registered HCPs in scope × 100 | Universe includes HCPs with zero contacts; 100 HCPs per territory |
| Contact concentration | Contacts received by the most-contacted 25% of registered HCPs / all contacts × 100 | HCP ID breaks ties; selected scope defines the quartile |
| Observed share of voice | Lumora observed contact count / total observed contacts across Lumora, Velaris and Arcelia × 100 | Withheld if any selected territory has missing/delayed status or expected brand rows are missing |
| Service promoter score | 100 × (promoters scoring 9–10 − detractors scoring 0–6) / valid responses; passives score 7–8 | Withheld if a selected survey delivery is missing or expected counts fail |
| Invitation/response denominator | 30 invited HCPs per delivered territory-month; 20 valid voluntary responses | Invitation total is withheld for incomplete selected scopes; valid response rows remain inspectable |

Targets are synthetic beginning-of-year plans: seasonality and annual demand assumptions allocate the annual target into month/territory components. Set date is January 1 of the relevant year, including the first partial calendar year in the dataset. Values are frozen; investigation never modifies them. Rounding occurs at category/territory/month grain, then national values sum the rounded rows.

The generator applies 5% annual baseline growth, a small seasonal curve, and 2026 engagement uplift. Additional deterministic patterns begin in April 2026. These assumptions make a coherent test market; they are not fitted to public, employer or patient data. The market does not model clinical stages, lines of therapy, eligibility, efficacy, survival, individual HCP decisions, spend or revenue.

Survey respondents are sampled from the registered HCP universe. Thirty invitations are a documented generator assumption rather than individual invitation rows. The service survey is voluntary, small, and repeated across months; it is neither representative population sentiment nor independent observations across time. A missing file is distinct from a zero response score.

Competitor activity is an observed-feed proxy with equal channel weights, independent of patient aggregate counts. Ashford's August/September competitor feed is deliberately absent. National share of voice is withheld rather than reweighting the delivered territories. Fairmont's August survey delivery is absent. September is uniformly 18/30 days across territories. No linear full-month extrapolation is made.

Field notes are fabricated anecdotes, intentionally capable of generating hypotheses. Statements such as “reported authorization checklist delay” refer to a made-up process. No medical or access rules are represented. Similar trends, changed activity and reported process friction do not establish causality.

The reference case numbers are stable for seed 73021, generator version 1.0. Changing the seed changes activity distribution, competitor contacts and surveys; fixed assertions and screenshots then need regeneration.
