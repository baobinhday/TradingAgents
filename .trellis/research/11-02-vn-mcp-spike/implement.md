# Implementation Plan: Spike SSI and TCBS MCP Access

**Status:** Completed
<!-- Lifecycle: Planning -> In Progress -> Verification -> Completed (or Blocked) -->
**PRD Reference:** [prd.md](./prd.md)
**Design Reference:** [design.md](./design.md)

## 1. Ordered Implementation Checklist
*(Execute directly in the active session: verify each step and tick `[x]` as progress is made)*

- [x] Complete SSI OAuth PKCE flow from Python client
- [x] Record SSI access and refresh token lifetimes and unattended refresh
- [x] Extract and document `tools/list` and catalog resources for SSI MCP
- [x] Verify OHLCV columns, raw and adjusted prices on SSI
- [x] Probe TCBS MCP discovery endpoint and evaluate backend viability
- [x] Determine go/no-go recommendation for TCBS MCP (no-go due to Cloudflare challenge)
- [x] Probe AlgoLab MCP endpoints and evaluate data coverage
- [x] Verify UPCoM tickers and news date filtering on SSI
- [x] Synthesize findings into `research/spike-findings.md` and `research/algolab-findings.md`

---

## 2. Risk Watchlist
- Cloudflare Managed Challenge blocking unattended backend clients
- Token expiration without unattended refresh grant
