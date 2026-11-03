# Journal - hieuht33 (Part 1)

> AI development session journal
> Started: 2026-10-29

---



## Session 1: Add Web UI for Backtest and Config
<!-- trellis-session: v=2 fp=b236393a68797b23 -->

**Date**: 2026-11-02
**Task**: Add Web UI for Backtest and Config
**Branch**: `dev`

### Summary

Build and integrate a modern Vite + React + shadcn/ui frontend with a FastAPI backend for configuring and running backtests with live SSE progress, provider model auto-fetching, and symbol normalization.

### Git Commits

| Hash | Message |
|------|---------|
| `0f4990d` | feat(web): add web console for configuration and backtesting |

### Status

[OK] **Completed**


## Session 2: Spike AlgoLab, SSI and TCBS MCP access
<!-- trellis-session: v=2 fp=e8d49f4a4bdf1031 -->

**Date**: 2026-11-03
**Task**: Spike AlgoLab, SSI and TCBS MCP access
**Branch**: `dev`

### Summary

Connect and evaluate AlgoLab, SSI, and TCBS MCP servers for Vietnamese market data. Verify Streamable HTTP POST transport, OAuth PKCE and API key authentication, 30-day token lifetime with unattended refresh, full OHLCV daily bars, and historical news pagination. Designate AlgoLab as primary for prices/indices and SSI as fallback/co-source for fundamentals and news. TCBS ruled out due to Cloudflare challenge and mobile iOTP requirements.

### Git Commits

| Hash | Message |
|------|---------|
| `f188b4c` | feat(vietnam): spike AlgoLab, SSI and TCBS MCP connectivity and schemas |
| `0b557fc` | docs(task): update Vietnam market epic tasks with AlgoLab and SSI findings |

### Status

[OK] **Completed**
