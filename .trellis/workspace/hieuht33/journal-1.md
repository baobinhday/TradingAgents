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


## Session 3: Vietnam market routing foundation and Yahoo call sites elimination
<!-- trellis-session: v=2 fp=bc55af6d927f8a86 -->

**Date**: 2026-11-03
**Task**: Vietnam market routing foundation and Yahoo call sites elimination
**Branch**: `dev`

### Summary

Added market='VN'|'US' abstraction across config, API schemas, and state. Decoupled agents/context.py, agents/tools.py, and memory/settlement.py from direct Yahoo imports. Updated symbol normalization and benchmark resolution for Vietnam (VNINDEX). Verified zero Yahoo calls for market='VN' with 1,450 passing unit tests.

### Git Commits

| Hash | Message |
|------|---------|
| `3228d33` | feat(vietnam): market-aware routing foundation and eliminate direct Yahoo call sites |

### Status

[OK] **Completed**


## Session 4: Implement AlgoLab and SSI MCP Vendor Adapters
<!-- trellis-session: v=2 fp=9a598706d4969737 -->

**Date**: 2026-11-03
**Task**: Implement AlgoLab and SSI MCP Vendor Adapters
**Branch**: `dev`

### Summary

Implemented official vendor integration for Vietnam stock market support (11-02-vn-mcp-vendors). Built AlgoLab MCP client with TTL caching and SSE stream parsing, and SSI MCP client with OAuth token store, single-use refresh token rotation, and rate limiter. Implemented market adapters with zero-volume unfinished bar filtering, fundamentals, financial statements, news, macro, technical indicators, and verified market snapshot. Wired whole-series price fallback and multi-source co-sourcing with URL/title deduplication into router. Added 18 unit tests; all 1,468 tests green.

### Git Commits

| Hash | Message |
|------|---------|
| `97dcd30` | feat(vietnam): implement AlgoLab and SSI MCP vendor adapters |

### Status

[OK] **Completed**


## Session 5: Vietnam Agent Context, Market Rules, Reporting Lag & Social Placeholder
<!-- trellis-session: v=2 fp=d1ddddebd61fe1e0 -->

**Date**: 2026-11-03
**Task**: Vietnam Agent Context, Market Rules, Reporting Lag & Social Placeholder
**Branch**: `dev`

### Summary

Implemented Vietnam equity market trading rules, simulated statutory reporting lag for financial statements, social analyst unavailable placeholder, and multi-source co-sourcing prompts.

### Main Changes

- Injected Vietnam market rules (HOSE +-7%, HNX +-10%, UPCoM +-15%, T+2.5, VND, foreign room) into instrument context
- Created vn_lag.py with 45-day quarterly and 90-day annual simulated statutory reporting lag filtering
- Applied reporting lag filter to AlgoLab and SSI financial statements and withheld live valuation profile on historical dates
- Implemented structured Social Analyst placeholder for Vietnam equities with zero network/LLM calls
- Updated News and Fundamentals Analyst prompts for source window limits and multi-source co-sourcing comparison

### Git Commits

| Hash | Message |
|------|---------|
| `3088b67` | feat(vietnam): implement Vietnam market rules, reporting lag, and social placeholder |

### Testing

- [OK] Added 16 unit tests in test_vn_agent_context.py covering rules, lag filtering, social placeholder, and conflicting figures
- [OK] Ran all 1,484 tests in project test suite (all green) and verified ruff lint checks

### Status

[OK] **Completed**

### Next Steps

- Proceed to Subtask 5 (11-02-vn-integration-backtest): end-to-end integration and backtesting for Vietnam market
