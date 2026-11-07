# PRD: Vietnam Stock Market Support via SSI and TCBS MCP

**Status:** Completed
<!-- Lifecycle: Draft -> In Review -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-02-vietnam-market-support/`

## Goal

Run the TradingAgents pipeline on Vietnamese equities with the same agent workflow used for global stocks. Vietnamese data comes only from AlgoLab MCP and SSI MCP.

## Confirmed Decisions

- Vietnamese tickers never reach Yahoo, through the router or any direct call site (user decision: Yahoo does not cover enough tickers).
- Prices and VN-Index: AlgoLab MCP is primary, SSI MCP is the fallback.
- News, analysis and other non-price data (financial statements, ratios, broker research, corporate events, foreign flows) are fetched from both AlgoLab and SSI and passed to agents side by side for debate. Data only one source offers comes from that source.
- TCBS MCP is out of scope: no unattended backend access is possible, because discovery is unreachable from a backend client.
- The Vietnam social analyst is a placeholder in this project; a real implementation belongs to a later phase.
- US and other existing markets keep their current behavior.
- The Vietnam historical data window is a configurable setting with a default of 730 days. No local data store in the first release.

## Confirmed Facts (Post-Spike)

### SSI MCP (`research/spike-findings.md`, `research/ssi-mcp-tools.txt`, `research/ssi-mcp-resources.txt`)

- Endpoint `https://mcp.ssi.com.vn/mcp`; 56 read-only tools and 9 reference resources; free with a valid SSI account.
- **Transport**: Streamable HTTP POST (`POST /mcp` returning SSE `data: {"result": ...}` with `Content-Type: application/json` and `Authorization: Bearer <token>`).
- **OAuth & Tokens**: RFC 7591 Dynamic Client Registration (`/oauth/register`) and RFC 7636 PKCE S256 verified. Access token lifetime is 30 days (2,592,000s). Refresh token grant works unattended with single-use refresh token rotation.
- **Market Data**:
  - `marketdata_list_stock_daily_data` provides full OHLCV (`open`, `high`, `low`, `close`, `volume`, `trading_date`).
  - `marketdata_list_daily_stock_infor` provides both raw and adjusted prices (`close_price_adjusted` vs `close_raw`), daily trading bands, and foreign net flows.
  - HOSE and HNX samples work without ticker prefixes. UPCoM is not verified: the sample `BSR` is on HOSE.
  - Index daily quotes supported via `marketdata_list_index_daily_data` (`VNINDEX`, `VN30`, `HNX30`).
- **News**: One call covers at most 6 months (`range` must be `1m`, `3m`, or `6m`). The tool schema says older news is reached by moving `to` back; this is not tested yet.
- **Financials**: Financial statements (`marketdata_list_finance_*`) and ratios (`fundamental_list_financial_ratios`) report `year_report` and `length_report` (1..4 = Q1..Q4, 5 = FY) with `is_audit`, but carry no publication timestamp. Lookahead protection requires a simulated reporting lag (45/90 days).
- **Rate Limits**: Rate limit observed at ~2 requests/second. Enforces `RATE_LIMITED` response with `retryAfterSeconds: 2`.
- `research_*` covers the SSI100 basket only. Macro coverage is bank interest rates and FX only.

### TCBS MCP (`research/spike-findings.md`, `research/tcbs-mcp-doc.txt`, source PDF in `tmp/`)

- Endpoint `https://mcp.tcbs.com.vn/mcp/tcinvest/`.
- Unauthenticated requests and all OAuth discovery endpoints return HTTP 302 redirecting to `https://www.tcbs.com.vn/` which is guarded by Cloudflare Managed Challenge (Turnstile / JS challenge), blocking automated headless scripts.
- Connection requires interactive browser login plus iOTP. How often iOTP is required is not documented.
- **Status: NO-GO for unattended backend integration.**

### AlgoLab MCP (`../11-02-vn-mcp-spike/research/algolab-findings.md`)

- Evaluated as GO for unattended use with an API key.
- The user has a free (Lite) account and an API key. The key is supplied through the `ALGOLAB_API_KEY` environment variable and is never stored in the repository.
- Lite quota is a system-wide shared pool of 1,000 calls per day, capped at 200 calls per person in 5 hours (docs, not load-tested).

### Current code

- Direct Yahoo call sites that bypass the router: `tradingagents/agents/context.py:9`, `tradingagents/agents/tools.py:15`, `tradingagents/memory/settlement.py:11`.
- `tradingagents/dataflows/router.py` selects vendors globally; `tradingagents/dataflows/symbols.py` normalizes for Yahoo only.
- `tradingagents/default_config.py` `benchmark_map` has no Vietnam entry.
- `tradingagents/api/schemas.py:13` models `asset_type` as stock or crypto, with no market field.
- The `mcp` Python package is not required for production runtime since Streamable HTTP POST transport uses standard `httpx`.
- `tradingagents/dataflows/date_window.py` already has `coverage_gap` and `withhold_live_profile` point-in-time helpers.
- `tmp/` has been added to `.gitignore`.

## Requirements

- R1. A user can choose the Vietnam market explicitly, in CLI, API and Web UI. A bare `VNM` is unambiguous once the market is chosen.
- R2. Prices, indicators, snapshot, identity, financials, news, insider data, benchmark and settlement all resolve through AlgoLab or SSI for Vietnam.
- R3. HOSE, HNX and UPCoM tickers are supported, subject to what the sources return.
- R4. Alpha for Vietnam is measured against VN-Index.
- R5. Bank and non-bank companies use the correct statements and ratios, and false zeros are not shown as values.
- R6. Agents receive Vietnam trading rules and Vietnam-relevant inputs: foreign flows, insider deals, corporate events, peers, analyst recommendations, bank rates and FX.
- R7. For Vietnam, the social analyst makes no Reddit, StockTwits or LLM call, returns a fixed "sentiment data unavailable" report, and downstream agents do not treat it as neutral sentiment.
- R8. Historical runs receive no data dated after the run date. Current-only tools are withheld, and uncovered windows are reported as unavailable.
- R8a. Vietnam backtests read the data window from configuration (default 730 days) and warn when a requested date or its indicator lookback falls outside it.
- R9. OAuth tokens are stored encrypted, never logged, and never sent to the Web UI.
- R9a. `ALGOLAB_API_KEY` is read from the environment and never logged or sent to the Web UI.
- R10. MCP calls have retry, caching and rate limiting, and map failures onto the existing typed vendor errors.
- R11. Price and index fallback happens per series: a run never splices bars from two vendors into one series, and the snapshot, indicators, settlement and benchmark state which vendor served them.
- R12. Multi-source data keeps each source labeled and does not average or silently reconcile differing values. Duplicate news is removed. One source failing leaves the other source's data and an explicit unavailable note.
- R13. Debating agents see where sources agree and differ, and cite the source of a figure they use.

## Acceptance Criteria

- [x] An analysis of a HOSE, an HNX and an UPCoM ticker completes end to end with no call to Yahoo, verified by a test that fails on any Yahoo access for market Vietnam.
- [x] A decision on a Vietnamese ticker settles with raw return and alpha against VN-Index.
- [x] A bank and a non-bank ticker each produce a correct fundamentals report.
- [x] A Vietnam run with `social` selected makes no social or LLM call for that node and shows the placeholder report.
- [x] A backtest on a past date passes a test proving no withheld tool or future-dated row reached an agent.
- [x] Outside the data window, a run reports the data as unavailable instead of failing or inventing values.
- [x] The existing test suite passes, and US ticker runs use their previous vendors.
- [x] No token or API key appears in logs or API responses.
- [x] With AlgoLab unavailable, a run gets prices and VN-Index from SSI, within SSI's window, and reports the vendor used.
- [x] A test proves no price series mixes bars from two vendors.
- [x] News and fundamentals reports show labeled data from both sources, and a report still completes when one source fails.

## Child Tasks

Run in this order; each later child depends on the ones before it.

1. `11-02-vn-mcp-spike`: verify access, tools, schemas, limits and history depth.
2. `11-02-vn-market-foundation`: market concept, routing, direct call sites (R1, R3).
3. `11-02-vn-mcp-vendors`: MCP clients, credentials, adapters, benchmark, multi-source fetch (R2, R4, R5, R9, R9a, R10, R11, R12).
4. `11-02-vn-agent-context`: rules, new tools, social placeholder, source-aware debate (R6, R7, R13).
5. `11-02-vn-backtest-web`: backtest, CLI and Web UI (R1, R8, R8a).

## Out of Scope

- A real Vietnam social sentiment source.
- Order placement or reading personal portfolios.
- Bonds, covered warrants and derivatives.
- Fetching Vietnamese data from Yahoo.
- TCBS MCP integration.

## Deferred

- A local long-term data store. The vendor cache stays extensible so this can be added later.
- AlgoLab and SSI policy on automated calls and long-term data retention. This needs a direct answer from each provider before any local store is built.
