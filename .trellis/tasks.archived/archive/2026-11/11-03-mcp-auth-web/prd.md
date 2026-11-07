# Fix AlgoLab/SSI news co-sourcing & add Web MCP auth management

## Goal

Fix the `slice(None, 10, None)` KeyError in AlgoLab `get_global_news`, resolve Cloudflare 403 blocks and pageSize validation errors in SSI MCP, and build a Web UI MCP management console with 1-click SSI OAuth PKCE authentication and key management.

## Requirements

1. **AlgoLab News Parsing**:
   - In `tradingagents/dataflows/vendors/algolab/news.py`, normalize `items` when AlgoLab returns tabular columnar format `{"columns": [...], "rows": [...]}` (standard for `kind="recap"` and `kind="expert"`).
   - In `_format_articles`, handle recap news without explicit `title` by extracting from `content`, and include the report content.
   - Set standard User-Agent on AlgoLab HTTP requests.

2. **SSI MCP Authentication & Transport**:
   - In `tradingagents/dataflows/vendors/ssi/client.py`, set a realistic browser User-Agent on all `httpx` requests to prevent Cloudflare WAF 403 blocks.
   - In `tradingagents/dataflows/vendors/ssi/news.py`, clamp `pageSize` to valid options: `[10, 20, 50, 100]` to avoid `VALIDATION_FAILED` errors.

3. **Web API for MCP Management (`/api/mcp`)**:
   - `GET /api/mcp/status`: Return status for SSI MCP, AlgoLab MCP, and other vendors.
   - `POST /api/mcp/ssi/auth/start`: Start OAuth 2.0 PKCE flow, generate state/verifier, return authorization URL.
   - `GET /api/mcp/ssi/callback`: Handle OAuth callback, exchange authorization code for tokens, save tokens to `~/.tradingagents/ssi_tokens.json` & fallback path.
   - `POST /api/mcp/ssi/tokens`: Direct token paste/save.
   - `POST /api/mcp/ssi/test`: Test SSI MCP connection.
   - `POST /api/mcp/algolab/key`: Update and persist `ALGOLAB_API_KEY`.
   - `POST /api/mcp/algolab/test`: Test AlgoLab MCP connection & return quota.

4. **Web UI MCP Management**:
   - Add a dedicated "Data & MCP" tab in `App.tsx` and a quick status indicator/button in `ConfigPanel`.
   - Provide 1-Click "Connect SSI MCP (OAuth)" button that launches popup and updates status upon authorization.
   - Provide manual token paste modal/inputs for SSI MCP.
   - Provide AlgoLab API Key input with visibility toggle and "Test Connection" button.
   - Show live connection badges and remaining quotas.

## Acceptance Criteria

- [ ] `get_global_news` succeeds for AlgoLab without raising `KeyError: slice(None, 10, None)`.
- [ ] `get_global_news` and `call_rpc` succeed for SSI without Cloudflare 403 blocks or pageSize validation errors.
- [ ] Co-sourcing `get_global_news` returns combined markdown from both AlgoLab and SSI when both are active.
- [ ] Web API `/api/mcp/*` endpoints are registered and functioning.
- [ ] Frontend displays the MCP management tab with 1-click SSI OAuth and key inputs.
- [ ] Unit and integration tests pass.
