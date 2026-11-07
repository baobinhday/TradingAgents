# Implementation Plan: Vietnam Agent Context & Market Rules

## Work Breakdown

### Phase 1: Market Rules & Context Injection
- [x] Update `tradingagents/agents/context.py`:
  - Enhance `build_instrument_context` with Vietnam market rules (HOSE $\pm7\%$, HNX $\pm10\%$, UPCoM $\pm15\%$, T+2.5, VND, foreign room, source citation).
  - Ensure `resolve_instrument_context` in `tradingagents/graph/trading_graph.py` passes `market=market` to `build_instrument_context`.

### Phase 2: Point-in-Time Financial Statements & Simulated Reporting Lag
- [x] Create `tradingagents/dataflows/vendors/vn_lag.py` (or integrate in date_window):
  - `get_vn_period_publication_date(period_str)`: 45 days for quarterly, 90 days for annual.
  - Filter statements in AlgoLab `fundamentals.py` and SSI `fundamentals.py` against `as_of_date`.
  - Withhold live valuation profile in `get_fundamentals` for historical dates (`is_historical(as_of_date)`).

### Phase 3: Social Analyst Placeholder
- [x] Update `tradingagents/agents/analysts/sentiment_analyst.py`:
  - Intercept `market == "VN"` or symbol `.VN`.
  - Return standardized `SENTIMENT_DATA_UNAVAILABLE` report without invoking Reddit, StockTwits, or LLM.
- [x] Update `tradingagents/agents/schemas.py`:
  - Support `UNAVAILABLE = "Unavailable"` in `SentimentBand` if needed.

### Phase 4: Source-Aware Prompts for Analysts & Debaters
- [x] Update `tradingagents/agents/analysts/news_analyst.py`:
  - Remind agent of Vietnam macro sources and window limits.
- [x] Update `tradingagents/agents/analysts/fundamentals_analyst.py`:
  - Remind agent of reporting lag and co-sourced data comparison.

### Phase 5: Testing & Verification
- [x] Unit tests in `tests/test_vn_agent_context.py`:
  - Test `build_instrument_context` includes VN market rules and source attribution for `market="VN"`.
  - Test simulated publication lag filtering on quarterly and annual statements.
  - Test Social Analyst placeholder outputs standardized signal without external or LLM calls.
  - Test multi-source conflicting figures reporting.
  - Test full test suite (`uv run pytest`) and linting (`uv run ruff check`).
