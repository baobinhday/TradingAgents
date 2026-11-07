# Implementation Plan: AlgoLab and SSI MCP Vendor Integration

**Status:** Completed
<!-- Lifecycle: Planning -> In Progress -> Verification -> Completed (or Blocked) -->
**PRD Reference:** [prd.md](./prd.md)
**Design Reference:** [design.md](./design.md)

## 1. Ordered Implementation Checklist

### Phase 1: Transport Clients & Auth
- [x] Create `tradingagents/dataflows/vendors/ssi/client.py`:
  - Streamable HTTP POST client (`POST https://mcp.ssi.com.vn/mcp`).
  - Token store: read/write token cache in `~/.tradingagents/ssi_tokens.json` (fallback to `scripts/spike_mcp/.ssi_auth_cache.json` if present).
  - Token rotation: unattended refresh grant on 401 or expiration; atomic token file update on RFC 6749 single-use rotation.
  - Rate limiting: paced queue (~2 req/s) with exponential backoff on `RATE_LIMITED` (`retryAfterSeconds`).
  - Typed error mapping (`VendorNotConfiguredError` if unauthenticated, `VendorUnavailableError` on 5xx/timeouts, `NoMarketDataError`).
- [x] Create `tradingagents/dataflows/vendors/algolab/client.py`:
  - Streamable HTTP POST client (`POST https://mcp.algolab.vn`).
  - Authentication: `Authorization: Bearer <ALGOLAB_API_KEY>` from environment (`.env`).
  - Required header: `Accept: application/json, text/event-stream`.
  - Cache: memory + file cache to bound request volume within Lite quota (200 calls / 5 hrs).
  - Response parsing: `{status, data, meta}`, handling `meta.quota`, `error.code`, and `SESSION_LIMIT`.
  - Typed error mapping (`VendorNotConfiguredError` if missing `ALGOLAB_API_KEY`, `VendorUnavailableError`, `NoMarketDataError`).

### Phase 2: Vendor Adapters (Market, Fundamentals, News, Macro)
- [x] Create `tradingagents/dataflows/vendors/ssi/market.py`:
  - `get_stock_data(symbol, start_date, end_date)`: OHLCV via `marketdata_list_stock_daily_data`.
  - `get_closes(symbol, start_date, end_date)`: Close prices series for stock or `VNINDEX`.
  - `get_index_daily_bars(symbol, start_date, end_date)`: `marketdata_list_index_daily_data`.
- [x] Create `tradingagents/dataflows/vendors/ssi/fundamentals.py`:
  - `get_company_profile(ticker)`: `fundamental_get_company_profile`.
  - `get_fundamentals(ticker, as_of_date)`: `fundamental_list_financial_ratios`.
  - `get_balance_sheet`, `get_cashflow`, `get_income_statement`.
- [x] Create `tradingagents/dataflows/vendors/ssi/news.py`:
  - `get_news(ticker, as_of_date)`: `marketdata_list_company_news` with `to` parameter pagination.
  - `get_global_news(as_of_date)`: `marketdata_list_market_news`.
- [x] Create `tradingagents/dataflows/vendors/algolab/market.py`:
  - `get_stock_data(symbol, start_date, end_date)`: `get_price_history`. Drop zero-volume unfinished session bars.
  - `get_closes(symbol, start_date, end_date)`: `get_price_history`.
- [x] Create `tradingagents/dataflows/vendors/algolab/fundamentals.py`:
  - `get_company_profile(ticker)`: `get_company_profile`.
  - `get_fundamentals(ticker, as_of_date)`: `get_company_profile` + `get_sector_valuation`.
  - `get_balance_sheet`, `get_cashflow`, `get_income_statement`: `get_financial_statements`.
- [x] Create `tradingagents/dataflows/vendors/algolab/news.py`:
  - `get_news(ticker, as_of_date)`: `get_news`.
  - `get_global_news(as_of_date)`: `get_news(kind="recap")`.
  - `get_insider_transactions`: `get_corporate_events`.
- [x] Create `tradingagents/dataflows/vendors/algolab/macro.py`:
  - `get_macro_indicators(indicator, as_of_date, look_back_days)`: `get_macro`.

### Phase 3: Multi-Source Co-Sourcing & Router Integration
- [x] Update `tradingagents/dataflows/router.py`:
  - Wire `algolab` and `ssi` vendor implementations into `VENDOR_METHODS`.
  - Implement whole-series fallback for `get_stock_data` and `get_closes`: AlgoLab primary, SSI fallback.
  - Implement multi-source aggregation for `news_data` and `fundamental_data` when both sources are configured (labeled sections, news deduplication).
  - Update `get_verified_market_snapshot` and `get_company_profile` to use AlgoLab/SSI.

### Phase 4: Testing & Verification
- [x] Unit tests in `tests/test_vn_mcp_vendors.py`:
  - Test AlgoLab client & error mapping with mock SSE responses.
  - Test SSI client, OAuth token rotation & rate limiting with mock SSE responses.
  - Test price series whole-series fallback (AlgoLab fails -> SSI serves entire series).
  - Test zero-volume bar dropping.
  - Test multi-source labeled output and news deduplication.
  - Verify secrets never appear in logs or exceptions.
- [x] Run full test suite (`uv run pytest`) and linting (`uv run ruff check`).
