# 40-second recruiter walkthrough

Persistent overlay: **Demo · Synthetic data**. Use August 2026 and Nordhaven. The shipped video is an edited sequence of actual UI still captures, captioned; it is not a continuous screen recording. It shows the offline evidence assistant, with the mode label visible. No narration should imply a live language model or an authenticated Snowflake session.

| Time | Visual / action | Caption or optional voice-over |
| --- | --- | --- |
| 0–5s | Opening question over the dashboard | “More HCP engagement. Fewer starts than planned. What changed?” |
| 5–10s | Market dashboard, then Nordhaven | “Nordhaven: 217 starts against 340 targeted, despite 38% more engagement.” |
| 10–15s | Investigate action and answer | “Start with the gap. Then investigate the evidence.” |
| 15–21s | Source-backed start mix | “Incoming switches explain 71.5% of the shortfall.” |
| 21–27s | Engagement evidence and field note source | “89.8% of contacts reach the top quarter of HCPs. Reported process delays are a hypothesis.” |
| 27–35s | Follow-up: “What should we investigate next?” | “Audit reach. Validate reported delays. Test before recommending more activity.” |
| 35–40s | End card | “From a performance gap to a testable next question. Preetham Vooturi · GitHub.” |

More precise wording for voice-over: switches contribute to the arithmetic shortfall; they do not causally “explain” a patient outcome. The video's caption uses “account for” to preserve that distinction. Engagement growth is 38.1%; the shorter “38%” is rounding.

Caption source: [demo-captions.srt](../artifacts/demo-captions.srt). Rebuild the media using `python -m scripts.make_video` after obtaining current UI captures and installing the optional imageio-ffmpeg package. Keep all clips and claims in offline mode until live authentication and responses have been verified.

For a live screen recording: start the local server, select Nordhaven, record the dashboard and Investigate click, open P01/E01/F01 citations, ask the follow-up, then record the end card. Avoid showing browser profile details, local paths, account identifiers or secrets. The GitHub destination must be the verified repository URL, not an invented publication link.
