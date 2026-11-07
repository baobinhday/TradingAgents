# Technical Design: Fix AlgoLab/SSI News Co-sourcing & Add Web MCP Auth Management

**Status:** Completed
<!-- Lifecycle: Draft -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-03-mcp-auth-web/`
**PRD Reference:** [prd.md](./prd.md)

## 1. Architecture & Component Boundaries
- **News Parser Fix**:
  - Normalize AlgoLab tabular columnar format `{"columns": [...], "rows": [...]}` into dict records.
  - Set realistic User-Agent on all AlgoLab and SSI HTTP requests to bypass Cloudflare 403 blocks.
  - Clamp SSI `pageSize` to valid options `[10, 20, 50, 100]`.
- **Backend MCP Management API (`tradingagents/api/routes/mcp.py`)**:
  - `/api/mcp/status`: Vendor status, token validity, quotas.
  - `/api/mcp/ssi/auth/start`: Initiate OAuth 2.0 PKCE flow.
  - `/api/mcp/ssi/callback`: Token exchange and persistence to `~/.tradingagents/ssi_tokens.json`.
  - `/api/mcp/ssi/tokens`: Direct token paste.
  - `/api/mcp/algolab/key`: Update `ALGOLAB_API_KEY`.
- **Web UI Management (`web/src/components/McpPanel.tsx`)**:
  - "Data & MCP" tab in dashboard.
  - 1-click SSI OAuth popup and status indicator.
  - AlgoLab API key configuration and connection testing.
