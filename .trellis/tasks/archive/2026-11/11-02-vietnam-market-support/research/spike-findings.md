# SSI and TCBS MCP Spike Findings

> **Task**: `11-02-vn-mcp-spike` (Spike SSI and TCBS MCP access)  
> **Date**: 2026-11-03  
> **Author**: AI Assistant / Developer `hieuht33`  
> **Target**: Replace unverified assumptions in parent PRD with empirical evidence from authenticated MCP connections.

---

## 1. Executive Summary & Go / No-Go Decision

| Provider | Unattended Backend Feasibility | Status | Recommended Role |
| :--- | :--- | :--- | :--- |
| **SSI MCP** | **Feasible (GO)** | **Production Ready** | **Primary Source** for Vietnamese market data: daily OHLCV prices, intraday quotes, foreign flows, market index (VNINDEX, VN30), financial statements, financial ratios, company news, and corporate actions. |
| **TCBS MCP** | **Not Feasible (NO-GO)** | **Blocked** | Unattended backend access is not viable due to Cloudflare Managed Challenges on all discovery endpoints and mandatory mobile iOTP per session. As planned in the parent PRD fallback, TradingAgents will run exclusively on **SSI MCP**. |

---

## 2. Evidence by Requirement

### Requirement 1: OAuth Registration & Interactive Authentication Flow

* **SSI MCP**:
  * **Dynamic Client Registration (RFC 7591)**: Supported and verified.
    * Endpoint: `POST https://mcp.ssi.com.vn/oauth/register`
    * Supports public clients (`token_endpoint_auth_method: "none"`), `authorization_code`, and `refresh_token` grant types.
    * Registration successfully returned a client ID (e.g. `dcr-4343d350...`) without manual administrator approval.
  * **Authorization Flow**:
    * Endpoint: `GET https://mcp.ssi.com.vn/oauth/authorize`
    * Uses RFC 7636 PKCE (`code_challenge_method: S256`) and redirects to `https://accounts.ssi.com.vn/login`.
    * User completes login and consents to `market-data:read` scope.
    * Browser redirects to local callback `http://localhost:8080/callback?code=...`.
  * **Transport Discovery**:
    * Unlike traditional long-lived `GET /sse` transports, SSI MCP implements **Streamable HTTP POST transport** (`POST https://mcp.ssi.com.vn/mcp` with JSON-RPC payload and `Authorization: Bearer <token>`, returning `text/event-stream` with `data: {"result": ...}`).

* **TCBS MCP**:
  * Endpoint: `https://mcp.tcbs.com.vn/mcp/tcinvest/`
  * Unauthenticated requests to this endpoint, as well as `/.well-known/oauth-authorization-server`, `/.well-known/openid-configuration`, and `/.well-known/oauth-protected-resource` unconditionally return `HTTP 302 Found` redirecting to `https://www.tcbs.com.vn/`.
  * The redirect destination is intercepted by Cloudflare Managed Challenge (Turnstile / JavaScript challenge `cf-mitigated: challenge`, HTTP 403), blocking programmatic OAuth discovery.
  * Connecting to TCBS is designed specifically for third-party AI UI connectors (Claude.ai / ChatGPT plugins) where an end-user performs interactive authentication plus in-app iOTP verification on the TCInvest mobile application.

---

### Requirement 2: Token Lifetimes & Refresh Mechanics

* **SSI MCP**:
  * **Access Token**:
    * Format: JWT (JSON Web Token), length 403 bytes.
    * Lifetime (`expires_in`): **2,592,000 seconds (30 days / 720 hours)**.
  * **Refresh Token**:
    * Format: JWT.
    * Present: Yes.
    * Behavior: `POST https://mcp.ssi.com.vn/oauth/token` with `grant_type=refresh_token`.
    * **Works without user re-login or iOTP**. A refreshed request completed in 0.64s and issued a new 30-day access token.
    * **Refresh Token Rotation**: SSI enforces strict single-use Refresh Token Rotation (RFC 6749 §6). Once a refresh token is exchanged, the previous refresh token is immediately invalidated (`{"error": "invalid_grant"}`). The client application must store and rotate the new refresh token atomically.

* **TCBS MCP**:
  * Could not determine token lifetime programmatically due to Cloudflare challenge and lack of DCR. Document indicates tokens are issued per session and can be revoked via TCInvest "AI Connector" dashboard.

---

### Requirement 3: Tool Catalog & Resource Inspection

* **SSI MCP**:
  * **Tool Count**: Exactly **56 tools** available and active.
  * Full JSON schemas extracted and saved to [ssi_tools_schema.json](file:///home/b560/Project/test/TradingAgents/.trellis/tasks/11-02-vn-mcp-spike/research/ssi_tools_schema.json).
  * Major Tool Categories:
    * **Market Data (`marketdata_*`)**: 45 tools covering daily quotes, intraday trades, order flow, foreign ownership, broker recommendations, corporate actions, and market indices (`VNINDEX`, `VN30`, `HNX30`).
    * **Fundamental Analysis (`fundamental_*`)**: 5 streamlined financial tools (`fundamental_list_financial_ratios`, `fundamental_list_balance_sheet`, `fundamental_list_income_statement`, `fundamental_list_cash_flow`, `fundamental_get_key_metrics`).
    * **SSI Research (`research_*`)**: 6 tools for SSI100 ratings and quantitative FA/TA scores.
  * **Resource Count**: Exactly **9 static catalog resources** available.
  * Full resource list saved to [ssi_resources.json](file:///home/b560/Project/test/TradingAgents/.trellis/tasks/11-02-vn-mcp-spike/research/ssi_resources.json) and contents saved to [ssi_resource_contents.json](file:///home/b560/Project/test/TradingAgents/.trellis/tasks/11-02-vn-mcp-spike/research/ssi_resource_contents.json).

* **TCBS MCP**:
  * 48 documented tools listed in `research/tcbs-mcp-doc.txt`. Schemas could not be dynamically queried due to transport access restriction.

---

### Requirement 4: Daily OHLCV Price Data & Adjustments

* **SSI Tools Tested**:
  1. `marketdata_list_stock_daily_data`:
     * Parameters: `symbol`, `range` (valid: `1d`, `3m`, `6m`, `1y`, `max_range`), optional `toDate`, `pageSize`, `pageIndex`.
     * Response: Full OHLCV array (`open`, `high`, `low`, `close`, `volume`, `trading_date`).
     * Values are denominated in VND (e.g. `SSI`: open `19250`, high `19350`, low `18500`, close `18850`, volume `27277400`).
  2. `marketdata_list_daily_stock_infor`:
     * Returns detailed trading metrics including:
       * `open`, `high`, `low`, `close`, `volume`, `trading_date`
       * Price boundaries: `ceiling_price`, `floor_price`, `ref_price`, `avg_price`
       * Price changes: `price_changed`, `per_price_change`
       * **Price Adjustment**: Explicitly provides both adjusted and raw values:
         * `close_price_adjusted` vs `close_raw`
         * `open_raw`, `high_raw`, `low_raw`
       * **Foreign Flow**: `foreign_buy_volume_total`, `foreign_sell_volume_total`, `net_buy_sell_volume`, `foreign_current_room`.
     * Verdict: Fully satisfies trading agent requirements with both raw and split/dividend-adjusted price series.

---

### Requirement 5: TCBS Long-Term Candlestick Tool

* Tool: `tca-tcanalysis_tcanalysis_getLongTermCandleChart`
* Result: **Could not determine directly** due to TCBS network boundary (NO-GO). All required daily OHLCV and index history are readily provided by SSI MCP (`marketdata_list_stock_daily_data` and `marketdata_list_index_daily_data`).

---

### Requirement 6: News Date Window Limits

* **SSI Tool Tested**: `marketdata_list_company_news`
* Empirical Observations:
  * `range: "1m"` $\rightarrow$ **Success** (returns articles with timestamps, headlines, snippets).
  * `range: "3m"` $\rightarrow$ **Success**.
  * `range: "6m"` $\rightarrow$ **Success**.
  * `range: "1y"` $\rightarrow$ **Error**: `Invalid arguments: range must be one of: 1m, 3m, 6m`.
  * `range: "max_range"` $\rightarrow$ **Error**: `Invalid arguments: range must be one of: 1m, 3m, 6m`.
* **Conclusion**: SSI MCP strictly caps news lookback at **6 months (180 days)**. The News & Sentiment agents must not request windows $>6$ months.

---

### Requirement 7: Financial Statements & Publication Dates

* **SSI Tools Tested**:
  1. `fundamental_list_financial_ratios`:
     * Parameters: `symbol`, `pageSize` (`10, 20, 50, 100`), optional `yearReport`, `lengthReport` (1..4 = Q1..Q4, 5 = FY).
     * Returns key valuation and operating ratios: `pe`, `pb`, `eps`, `book_value`, `roe`, `roa`, `roic`, `gross_profit_margin`, `net_profit_margin`, `debt_to_equity`, `current_ratio`, `market_cap`.
  2. `marketdata_list_finance_income_statement`, `marketdata_list_finance_balance_sheet`, `marketdata_list_finance_cash_flow`:
     * Comprehensive line items (171 fields for income statements, 275 fields for balance sheets).
     * **Publication Date Observation**: Financial statements contain `year_report` and `length_report` (e.g. `year_report: 2025, length_report: 5, is_audit: "1"`), but **do not carry an explicit publication or announcement date**.
     * **Architectural Implication**: Point-in-time backtesting must apply a conservative reporting lag (e.g., 45 days after quarter-end or 90 days after fiscal year-end) using `date_window.py` to prevent lookahead bias.

---

### Requirement 8 & 9: Exchange & Sector Coverage, Rate Limits

* **Exchange Sampling**:
  * **HOSE**: `SSI` (Securities), `VCB` (Banking), `BVH` (Insurance) $\rightarrow$ **100% Success**.
  * **HNX**: `PVS` (Energy/Oil) $\rightarrow$ **100% Success**.
  * **UPCoM**: `BSR` (Refining) $\rightarrow$ **100% Success**.
  * All three exchanges are supported under standard 3-character ticker symbols without requiring special exchange prefixes in the `symbol` parameter.

* **Rate Limits**:
  * SSI enforces rate limiting per account token.
  * Observed behavior: When sending 5 rapid requests with 0.4s spacing, request 5 triggered:
    ```json
    {
      "code": "RATE_LIMITED",
      "message": "Rate limit exceeded",
      "retryAfterSeconds": 2
    }
    ```
  * **Architectural Implication**:
    * Implement a client-side token bucket or leaky bucket rate limiter capped at **2 requests per second**.
    * Respect the `retryAfterSeconds` field on `RATE_LIMITED` responses with exponential backoff.
    * Average latency per call under normal conditions: **0.12s – 0.35s**.

---

### Requirement 10: TCBS Personal Data vs Public Data Scope

* Per TCBS official documentation (Section 4 vs FAQ 13), personal portfolio and order data require individual user consent, but unauthenticated / backend client registration is not supported.
* Since TCBS is designated NO-GO for backend automation, no personal data access risks exist for TradingAgents.

---

## 3. Recommended Vendor Architecture for Subsequent Tasks

Based on the verified spike results:

```
+-------------------------------------------------------------+
|                      TradingAgents                          |
+-------------------------------------------------------------+
                               |
              Market Routing   | market == "VN"
                               v
+-------------------------------------------------------------+
|                   SSIMCPVendorAdapter                       |
|  - Transport: Streamable HTTP POST (https://mcp.ssi.com.vn) |
|  - Auth: OAuth 2.0 PKCE + 30-day Token + Auto-Refresh       |
|  - Rate Limiter: 2 req/sec + retryAfterSeconds backoff      |
+-------------------------------------------------------------+
        |                  |                    |
        v                  v                    v
+---------------+  +-----------------+  +---------------------+
| Prices/Quotes |  | Financials/Ratios| | News & Sentiment    |
| (OHLCV, Raw & |  | (Statements +   | | (<= 6-month window) |
|  Adjusted)    |  |  Ratios + Lag)  |  |                     |
+---------------+  +-----------------+  +---------------------+
```

* **Child Task `11-02-vn-market-foundation`**: Configure explicit `market="VN"` routing; eliminate direct Yahoo fallback for Vietnam.
* **Child Task `11-02-vn-mcp-vendors`**: Implement `SSIMCPVendor` using Streamable HTTP POST transport and persistent token rotation. TCBS adapter is scoped out.
* **Child Task `11-02-vn-agent-context`**: Bound news tools to 6-month max window and apply 45/90 day lag to financial statements.
* **Child Task `11-02-vn-backtest-web`**: Point-in-time checks enforce SSI 730-day max history and 6-month news boundary.

---

## Addendum: Review Corrections & Retest Results (2026-11-03)

### 1. UPCoM Retest on SSI (Requirement 12.1) — VERIFIED
* `BSR` had transitioned to HOSE. Tested with a verified UPCoM ticker: **`QNS`** (Đường Quảng Ngãi).
* Result: `marketdata_list_stock_daily_data` for `QNS` (range=3m) returned full OHLCV records successfully (e.g. `trading_date: 02/11/2026`, `open: 49400`, `high: 49400`, `low: 48900`, `close: 49400`, `volume: 159400`).
* **Verdict**: UPCoM support on SSI is fully functional without any ticker prefixes.

### 2. SSI News History Depth (Requirement 12.2) — VERIFIED
* Tested `marketdata_list_company_news` with parameter `to` set to historical dates:
  * `to: "01/01/2026"`, `range: "3m"` $\rightarrow$ Returned news articles from December 2025 (`30/12/2025`).
  * `to: "01/06/2025"`, `range: "3m"` $\rightarrow$ Returned news articles from May 2025 (`23/05/2025`).
* **Conclusion**: The 6-month limit (`range="6m"`) is strictly a **per-query span limit**, NOT a hard repository cap. Historical news across the entire 730-day window can be retrieved by paginating backward with the `to` parameter (formatted `DD/MM/YYYY`).

### 3. AlgoLab MCP Authenticated Probe — VERIFIED (GO)
* Tested `https://mcp.algolab.vn` using `ALGOLAB_API_KEY` from `.env`.
* Transport requirements:
  * Headers: `Authorization: Bearer <ALGOLAB_API_KEY>`, `Content-Type: application/json`, and `Accept: application/json, text/event-stream` (required, returns 406 if omitted).
  * Protocol: Streamable HTTP POST returning SSE event streams.
* Probes executed:
  * `initialize`: Server `algolab-market-data` v2.1.0 confirmed.
  * `tools/list`: All 12 primary tools active (`get_price_history`, `get_quotes`, `get_company_profile`, `get_financial_statements`, `get_research_reports`, `get_news`, `get_macro`, `get_intelligence`, etc.).
  * `get_price_history` for `VNM` (2026-10-25 to 2026-11-01): Returned tabular bars with columns `["t", "o", "h", "l", "c", "v", "value", "foreign_net", "foreign_net_val"]`.
  * Quota: Accurately reports daily quota in metadata (e.g. `quota: {'used': 42, 'limit': 1000}`).

### 4. TCBS Status
* Stands as NO-GO for unattended backend access due to Cloudflare Turnstile blocks and lack of DCR. All requirements are fully covered by AlgoLab (Primary for prices & index) and SSI (Fallback for prices, co-source for news/fundamentals).
