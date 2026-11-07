# Implementation Plan: Vietnam Stock Market Support via SSI and TCBS MCP

**Status:** Completed
<!-- Lifecycle: Planning -> In Progress -> Verification -> Completed (or Blocked) -->
**PRD Reference:** [prd.md](./prd.md)
**Design Reference:** [design.md](./design.md)

## 1. Ordered Implementation Checklist
*(Execute directly in the active session: verify each step and tick `[x]` as progress is made)*

- [x] Phase 1: Spike SSI and TCBS MCP access (`11-02-vn-mcp-spike`)
- [x] Phase 2: Market-aware routing foundation (`11-02-vn-market-foundation`)
- [x] Phase 3: AlgoLab and SSI MCP vendor integration (`11-02-vn-mcp-vendors`)
- [x] Phase 4: Vietnam agent context and market rules (`11-02-vn-agent-context`)
- [x] Phase 5: Vietnam backtest and Web UI integration (`11-02-vn-backtest-web`)

---

## 2. Risk Watchlist
- Vendor rate limits on SSI MCP (~2 req/s)
- AlgoLab Lite tier quota limits (200 calls / 5 hrs)
- Lack of publication timestamps on SSI financial statements requiring 45/90 day lag simulation
