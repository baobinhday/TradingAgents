# Technical Design: AlgoLab and SSI MCP Vendor Integration

**Status:** Completed
<!-- Lifecycle: Draft -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-02-vn-mcp-vendors/`
**PRD Reference:** [prd.md](./prd.md)

## Context and Scope

This task (`11-02-vn-mcp-vendors`) integrates Vietnam financial market data into the TradingAgents pipeline through two MCP providers:
1. **AlgoLab MCP** (`https://mcp.algolab.vn`): Primary source for stock and VN-Index OHLCV, valuation/profile, broker research, and financial statements. Keyless free tier exists, but official access uses `ALGOLAB_API_KEY` from environment.
2. **SSI MCP** (`https://mcp.ssi.com.vn/mcp`): Fallback for stock and VN-Index OHLCV; co-source for financial statements and corporate news (historical news paging back 730 days). Access uses OAuth Dynamic Client Registration (DCR) and PKCE with 30-day tokens and single-use refresh token rotation.
3. **TCBS MCP**: Out of scope (confirmed NO-GO due to Cloudflare Managed Challenges and iOTP requirement).

## Architectural Principles

1. **Vendor Encapsulation**:
   - `tradingagents/dataflows/vendors/ssi/`: Streamable HTTP POST client, OAuth token management, and data adapters.
   - `tradingagents/dataflows/vendors/algolab/`: Streamable HTTP POST client with `ALGOLAB_API_KEY`, quota tracking, response caching, and data adapters.
2. **Standard Error Mapping**:
   - All vendor failures map to typed `VendorError` subclasses (`VendorNotConfiguredError`, `VendorUnavailableError`, `NoMarketDataError`).
   - Secrets (`ALGOLAB_API_KEY`, SSI tokens) are strictly scrubbed from all logs and error messages.
3. **Price & Index Fallback (Whole-Series Only)**:
   - AlgoLab is primary; SSI is fallback.
   - Fallback operates per whole series, never per bar. A single series never mixes bars from multiple vendors.
   - Any placeholder bar with zero volume from an unfinished/in-progress session is filtered out.
4. **Multi-Source Aggregation (Side-by-Side Co-Sourcing)**:
   - For non-price data (news and fundamentals), data from both AlgoLab and SSI is fetched and labeled with source attribution for downstream debating agents.
   - News deduplication by canonical URL and normalized title.
   - Fail-open: if one source fails, the other source's data is delivered with an explicit labeled note about the failed source.
5. **Rate Limiting & Token Persistence**:
   - SSI client implements ~2 req/s paced queue with backoff on `RATE_LIMITED` (`retryAfterSeconds`).
   - SSI OAuth tokens persisted in user cache dir (`~/.tradingagents/ssi_tokens.json` or `.ssi_auth_cache.json`), updated atomically on single-use refresh token rotation.
   - AlgoLab client caches results to preserve the 200 req / 5 hr quota.

## Data Mapping Matrix

| Category | Method / Tool | AlgoLab Tool / Function | SSI Tool / Function | Fallback / Co-source Policy |
|---|---|---|---|---|
| `core_stock_apis` | `get_stock_data` | `get_price_history` (OHLCV) | `marketdata_list_stock_daily_data` | AlgoLab primary -> SSI whole-series fallback |
| `core_stock_apis` | `get_closes` | `get_price_history` | `marketdata_list_stock_daily_data` / `marketdata_list_index_daily_data` | AlgoLab primary -> SSI fallback |
| `core_stock_apis` | `get_verified_market_snapshot` | Derived from AlgoLab/SSI OHLCV + stockstats | Derived from SSI OHLCV | AlgoLab primary -> SSI fallback |
| `technical_indicators`| `get_indicators` | Derived from AlgoLab/SSI OHLCV + stockstats | Derived from SSI OHLCV | AlgoLab primary -> SSI fallback |
| `fundamental_data` | `get_fundamentals` | `get_company_profile` + `get_sector_valuation` | `fundamental_list_financial_ratios` | Co-source: both labeled side-by-side |
| `fundamental_data` | `get_balance_sheet` | `get_financial_statements(type="bs")` | `marketdata_list_finance_balance_sheet` | Co-source: both labeled side-by-side |
| `fundamental_data` | `get_cashflow` | `get_financial_statements(type="cf")` | `marketdata_list_finance_cash_flow` | Co-source: both labeled side-by-side |
| `fundamental_data` | `get_income_statement` | `get_financial_statements(type="is")` | `marketdata_list_finance_income_statement`| Co-source: both labeled side-by-side |
| `fundamental_data` | `get_company_profile` | `get_company_profile` | `fundamental_get_company_profile` | AlgoLab primary -> SSI fallback |
| `news_data` | `get_news` | `get_news` | `marketdata_list_company_news` (paged) | Co-source: deduplicated, both labeled |
| `news_data` | `get_global_news` | `get_news(kind="recap")` | `marketdata_list_market_news` | Co-source: both labeled |
| `news_data` | `get_insider_transactions` | `get_corporate_events` | `marketdata_list_daily_stock_infor` | Co-source: both labeled |
| `macro_data` | `get_macro_indicators` | `get_macro(vietnam)` | `marketdata_list_bank_interest_rates` | Co-source: both labeled |
