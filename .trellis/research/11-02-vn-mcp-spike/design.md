# Technical Design: Spike SSI and TCBS MCP Access

**Status:** Completed
<!-- Lifecycle: Draft -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-02-vn-mcp-spike/`
**PRD Reference:** [prd.md](./prd.md)

## 1. Architecture & Component Boundaries
- **Spike Scope**: Standalone scripts under `scripts/spike_mcp/` testing external broker MCP servers before writing application code.
- **SSI MCP**: Test RFC 7591 dynamic client registration, RFC 7636 PKCE S256 OAuth, token caching, tools discovery, OHLCV, and rate limiting.
- **TCBS MCP**: Test connection endpoint, Cloudflare challenge behavior, and authentication viability.
- **AlgoLab MCP**: Public documentation and anonymous `/free` probing.

---

## 2. Findings & Decisions
- SSI MCP: Production ready (GO).
- TCBS MCP: No-go for unattended backend due to Cloudflare challenge.
- AlgoLab MCP: Production ready (GO).
