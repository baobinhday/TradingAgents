# PRD: Vietnam Agent Context & Market Rules

**Status:** Completed
<!-- Lifecycle: Draft -> In Review -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-02-vn-agent-context/`

## Goal

Add Vietnam equity market rules, analyst tool capabilities, simulated reporting lag for financial statements, macro inputs, and a social analyst placeholder.

## Confirmed Spike Insights

- Financial statements do not carry publication timestamps; simulated reporting lag (45 days post quarter-end, 90 days post FY-end) must be injected into agent context to prevent lookahead bias.
- One SSI news call covers at most 6 months; AlgoLab news reached about 4 weeks in the FPT sample.
- Vietnam equities trade under standard T+2 settlement and ±7% (HOSE) / ±10% (HNX) / ±15% (UPCoM) price limits.

## Requirements

1. **Market Knowledge & Trading Rules**:
   - Trading hours: 9:00 - 15:00 UTC+7.
   - Price limit bands: HOSE ±7%, HNX ±10%, UPCoM ±15%.
   - Currency: VND.
2. **Point-in-Time Financial Statements**:
   - Filter statements visible to the Fundamental Analyst based on simulated publication lag (45 days for quarterly, 90 days for annual).
3. **News & Sentiment Agent Constraints**:
   - News windows follow what each source can serve, and uncovered windows are reported as unavailable.
4. **Social Analyst Placeholder**:
   - Provide a structured placeholder for Vietnam social media analysis (e.g. F319, Facebook groups, Telegram channels) that makes no social or LLM call, and returns an explicit "sentiment data unavailable" report. It is not a neutral signal, and downstream agents must not treat it as one.
5. **Source-Aware Debate**:
   - News, fundamentals and research reports present AlgoLab and SSI data as labeled sources.
   - Analysts report where sources agree and differ, without averaging or choosing silently.
   - Bull, bear and risk debaters may challenge a source and must cite the source of any figure they use.
   - Prompt length stays bounded, because two sources increase tokens per run.

## Acceptance Criteria

- [x] Fundamental Analyst prompt and tool invocations observe the reporting lag.
- [x] News Analyst handles source window limits without throwing validation errors.
- [x] A test fixture with conflicting source figures produces a report that shows both values with their sources.
- [x] Social Analyst placeholder cleanly outputs standardized signal without crashing the pipeline.
- [x] Unit tests verify prompt templates and context filtering for Vietnam market.
