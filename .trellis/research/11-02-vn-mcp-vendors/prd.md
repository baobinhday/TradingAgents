# PRD: AlgoLab and SSI MCP Vendor Integration

**Status:** Completed
<!-- Lifecycle: Draft -> In Review -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-02-vn-mcp-vendors/`

## Goal

Implement AlgoLab and SSI MCP clients and vendor adapters for Vietnamese data. AlgoLab serves prices and VN-Index with SSI as fallback; non-price data is fetched from both sources.

## Confirmed Spike Insights

- TCBS MCP is NO-GO due to Cloudflare Managed Challenges and in-app iOTP requirement. TCBS is out of scope.
- SSI MCP uses **Streamable HTTP POST transport** (`POST https://mcp.ssi.com.vn/mcp` returning SSE `data: {"result": ...}`).
- Token lifetime is 30 days. Single-use refresh token rotation is supported unattended.
- SSI client-side rate limiting at ~2 req/sec with `retryAfterSeconds` handling is required.
- AlgoLab limits and data caveats are in `../11-02-vn-mcp-spike/research/algolab-findings.md`.

## Requirements

1. **SSI MCP Transport & Token Client**:
   - Streamable HTTP POST client using `httpx`.
   - Token store: persist access and refresh tokens locally (e.g. encrypted or in secure user directory/cache).
   - Auto-refresh: when token is within expiration threshold or receives 401, refresh tokens and persist rotated tokens.
2. **Price Vendor Adapter**:
   - `get_daily_bars(symbol, start_date, end_date)`: maps to `marketdata_list_stock_daily_data` or `marketdata_list_daily_stock_infor`.
   - Returns normalized Pandas DataFrame with columns: `Open`, `High`, `Low`, `Close`, `Volume`.
   - Support raw vs adjusted close prices (`close_price_adjusted` vs `close_raw`).
3. **Index Vendor Adapter**:
   - `get_index_daily_bars("VNINDEX", ...)`: maps to `marketdata_list_index_daily_data`.
4. **Financials & Ratios Vendor Adapter**:
   - Map `fundamental_list_financial_ratios` for valuation and profitability metrics.
   - Map `marketdata_list_finance_income_statement`, `balance_sheet`, and `cash_flow`.
5. **News Vendor Adapter**:
   - Map `marketdata_list_company_news`, 6 months per call. Page older windows with `to` if the spike confirms it works.
6. **Rate Limiting & Resilience**:
   - Paced queue (2 req/s) with exponential backoff on `RATE_LIMITED`.
7. **AlgoLab Client**:
   - Same transport style, authenticated by `ALGOLAB_API_KEY` from the environment. A missing key raises the existing not-configured vendor error.
   - Handle `{status, data, meta}`, `error.code`, `meta.next_cursor`, `meta.clamped`, `meta.truncated` and `SESSION_LIMIT`.
   - Cache aggressively to protect the Lite quota.
8. **Price and Index Chain**:
   - `get_price_history` is primary and SSI is the fallback, for stock and `VNINDEX` series.
   - Fall back per whole series, never per bar. Record the serving vendor.
   - Drop placeholder bars with zero volume from an unfinished session.
9. **Multi-Source Fetch**:
   - The router currently returns the first vendor that succeeds. Add a mode for news and fundamentals categories that calls all configured vendors and returns labeled source sections.
   - One source failing yields a labeled unavailable section, not a run failure.
   - Deduplicate news by URL, then by normalized title.

## Acceptance Criteria

- [x] AlgoLab and SSI vendor adapters pass mock and unit tests with offline fixtures.
- [x] Live integration test can fetch daily bars for HOSE (`SSI`), HNX (`PVS`), and a verified UPCoM ticker.
- [x] Auto-refresh logic seamlessly rotates tokens without requiring re-authentication.
- [x] Rate limiter handles burst calls without unhandled 429 exceptions.
- [x] A failed AlgoLab price call falls back to SSI for the whole series.
- [x] Multi-source results stay labeled, and a single-source failure still returns the other source.
- [x] The API key never appears in logs or errors.
