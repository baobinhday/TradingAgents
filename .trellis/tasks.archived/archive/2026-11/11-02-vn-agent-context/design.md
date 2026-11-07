# Technical Design: Vietnam Agent Context & Market Rules

## Context and Scope

This task (`11-02-vn-agent-context`) enriches the multi-agent trading system with Vietnam equity market rules, point-in-time financial statement filtering with simulated disclosure lag, social sentiment placeholder handling, and source-aware multi-source debate.

## Architectural Components

### 1. Market Knowledge & Trading Rules (`context.py`)
- Injected into all agents via `build_instrument_context` when `market == "VN"` or symbol ends with `.VN`:
  - **Trading Session & Match**: 9:00 - 15:00 UTC+7 (lunch break 11:30 - 13:00); ATO (9:00 - 9:15), continuous matching, ATC (14:30 - 14:45), PLO.
  - **Daily Price Limits**: HOSE $\pm7\%$, HNX $\pm10\%$, UPCoM $\pm15\%$ (based on prior reference price / weighted average).
  - **Settlement**: Standard T+2.5 cycle (bought shares settle in afternoon of T+2).
  - **Currency**: Vietnamese Dong (VND).
  - **Foreign Ownership Limits (FOL)**: Room limits apply (e.g. 30% for banks, 49% or 100% for other sectors).
  - **Source Attribution**: Instruction to cite sources (`[Source: AlgoLab]`, `[Source: SSI]`) and explicitly debate divergences without silent averaging.
- Bounded length: Keeps context concise (~60 tokens) to prevent prompt bloat.

### 2. Point-in-Time Financial Statements & Simulated Reporting Lag
- **Spike Finding**: AlgoLab and SSI report statements by period (e.g. `2026-Q3`, `2025`) without disclosure timestamps.
- **Reporting Lag Rules**:
  - Quarterly statements: Public disclosure cutoff is 45 days post quarter-end:
    - Q1 (ends 03-31): Disclosed by May 15
    - Q2 (ends 06-30): Disclosed by August 14
    - Q3 (ends 09-30): Disclosed by November 14
    - Q4 (ends 12-31): Disclosed by February 14 (following year)
  - Annual statements: Audited annual disclosure cutoff is 90 days post fiscal year-end (ends 12-31 -> disclosed by March 31).
- **Enforcement**:
  - `filter_vn_financial_statements`: Filters columns (AlgoLab) or rows (SSI) with periods whose publication date is after `as_of_date`.
  - Withheld notice: If no statement was published on or before `as_of_date`, returns standardized point-in-time withheld notice.
  - Present-day valuation multiples: `withhold_live_profile(as_of_date)` withholds live profile for historical runs.

### 3. Social Analyst Placeholder (`sentiment_analyst.py`)
- When `market == "VN"` or symbol ends with `.VN`:
  - Skips all external social API calls (no Reddit, no StockTwits).
  - Skips LLM invocation (zero token cost, deterministic execution).
  - Emits standardized `SentimentReport` / text with `overall_band = Unavailable`, score `N/A`, confidence `Low`.
  - Explains explicitly: `SENTIMENT_DATA_UNAVAILABLE: Vietnam retail social media feeds (F319, Facebook groups, Telegram) are not connected. This is an absence of data, NOT a neutral signal. Downstream agents must not treat this as neutral or fabricate retail sentiment.`

### 4. Source-Aware Debate & Prompt Guidance
- **News Analyst**: Updated prompt guidance explaining Vietnam macro indicators (AlgoLab CPI, GDP, M2, FX, IIP) and source window handling.
- **Fundamental Analyst**: Updated prompt guidance explaining simulated reporting lags and comparing co-sourced figures.
- **Bull/Bear & Risk Debaters**: Receive source attribution instructions via `instrument_context` to cite figures and challenge discrepancies.
