# PRD: Spike SSI and TCBS MCP Access

**Status:** Completed
<!-- Lifecycle: Draft -> In Review -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-02-vn-mcp-spike/`

## Goal

Replace the unverified assumptions in the parent PRD with evidence from authenticated connections, before any production code depends on them.

## Requirements

Using a throwaway Python client outside the product code, and the user's own interactive login:

1. SSI first, then TCBS: complete OAuth from a Python client and record the client registration path and redirect handling.
2. Record access and refresh token lifetime, and whether refresh works without a new login or iOTP.
3. Save `tools/list` for both servers, including input schemas. For SSI, also read the catalog resources.
4. Check `marketdata_list_stock_daily_data` and `marketdata_list_daily_stock_infor`: are full OHLCV columns present, and are prices adjusted?
5. Check `tca-tcanalysis_tcanalysis_getLongTermCandleChart`: does it return bars or a link, what is the history depth, and does it accept an index code?
6. Check whether news can be fetched for windows older than 6 months.
7. Check whether statements carry a publication date.
8. Observe rate limits with a small, paced sample. Do not stress either service.
9. Sample HOSE, HNX and UPCoM tickers, plus bank, insurance and securities companies.
10. Check what the TCBS token can reach, to resolve the Section 4 versus FAQ 13 contradiction.

11. Evaluate AlgoLab MCP on the same criteria, without an account, using public docs and the anonymous `/free` endpoint.
12. Retest on SSI with an authenticated session: a real UPCoM ticker, and news older than 6 months using `to`.

## Acceptance Criteria

- [x] `research/spike-findings.md` answers each requirement with observed evidence or an explicit "could not determine".
- [x] A go or no-go for each provider on unattended backend use, with a recommended source for each data type.
- [x] Parent PRD and child PRDs are updated with the findings.
- [x] No token, account data or personal data is written to the repository.
- [x] `research/algolab-findings.md` records the AlgoLab evaluation.
- [x] Requirement 12 results are recorded.

## Findings Summary

- **SSI MCP**: **GO (Production Ready)**.
  - RFC 7591 Dynamic Client Registration (`/oauth/register`) and RFC 7636 PKCE S256 verified.
  - Streamable HTTP POST transport (`POST /mcp` returning SSE `data: {"result": ...}`).
  - Token lifetime: 30 days (2,592,000s). Refresh token rotation supported without interactive prompt.
  - 56 tools and 9 catalog resources fully mapped. Full OHLCV daily data, raw and adjusted prices, and foreign flows present.
  - News strictly capped at 6 months (`range: "6m"`). Financial statements lack publication dates; 45/90 day lag required for point-in-time safety.
  - Rate limits: ~2 requests/second; respects `retryAfterSeconds` on `RATE_LIMITED`.
- **TCBS MCP**: **NO-GO for unattended backend**.
  - All discovery and MCP endpoints redirect with 302 to homepage behind Cloudflare Managed Challenge (Turnstile / JS challenge).
  - Requires interactive login and in-app mobile iOTP per session.
  - Fallback adopted: All Vietnam data will be served by SSI MCP.
- **AlgoLab MCP**: **GO**, see `research/algolab-findings.md`. API key access, daily prices and index back to at least 2014 in samples, bank and insurance statement forms, macro series. News reached about 4 weeks in the FPT sample.
- Corrections to the SSI and TCBS findings are in the addendum of `research/spike-findings.md`.
