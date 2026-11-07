# Implementation Plan: Fix AlgoLab/SSI News Co-sourcing & Add Web MCP Auth Management

**Status:** Completed
<!-- Lifecycle: Planning -> In Progress -> Verification -> Completed (or Blocked) -->
**PRD Reference:** [prd.md](./prd.md)
**Design Reference:** [design.md](./design.md)

## 1. Ordered Implementation Checklist
*(Execute directly in the active session: verify each step and tick `[x]` as progress is made)*

- [x] Fix AlgoLab tabular columnar news parsing in `tradingagents/dataflows/vendors/algolab/news.py`
- [x] Add realistic browser User-Agent headers to SSI and AlgoLab HTTP clients
- [x] Clamp SSI news `pageSize` to valid options `[10, 20, 50, 100]`
- [x] Implement `/api/mcp` backend endpoints in `tradingagents/api/routes/mcp.py`
- [x] Implement SSI OAuth PKCE start and callback handlers
- [x] Implement Web UI "Data & MCP" panel and connection status cards
- [x] Add test suite for MCP routes and error handling

---

## 2. Risk Watchlist
- Cloudflare WAF heuristic blocks on non-browser user agents
- SSI OAuth popup blocker in user browsers
