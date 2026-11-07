# Technical Design: Vietnam Stock Market Support via SSI and TCBS MCP

**Status:** Completed
<!-- Lifecycle: Draft -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-02-vietnam-market-support/`
**PRD Reference:** [prd.md](./prd.md)

## 1. Architecture & Component Boundaries
- **Market Routing Foundation**: Introduce `market` concept ("US" vs "VN"). Route Vietnamese instruments strictly to AlgoLab and SSI MCP, never Yahoo Finance.
- **MCP Vendors**:
  - AlgoLab MCP: Primary price and OHLCV feed; co-sourced news and fundamentals.
  - SSI MCP: Fallback price feed; streamable HTTP POST with OAuth PKCE; co-sourced news and financial statements.
  - TCBS MCP: Evaluated in spike and marked no-go due to interactive Cloudflare challenge.
- **Vietnam Agent Context**: HOSE/HNX/UPCoM trading rules, floor/ceiling bands, T+2.5 settlement, foreign ownership room, and simulated 45/90 day reporting lag.
- **Backtest & Web UI**: Configurable 730-day historical window guard, VNINDEX benchmark, and full web dashboard integration.

---

## 2. Data Flow
```
[User / Web / CLI] ──► [TradingGraph] ──► [Market Router] ──► [AlgoLab MCP / SSI MCP]
```
