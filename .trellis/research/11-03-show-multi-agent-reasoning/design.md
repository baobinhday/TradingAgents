# Technical Design: Show Comprehensive Multi-Agent Reasoning in ResultsPanel

**Status:** Completed
<!-- Lifecycle: Draft -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-03-show-multi-agent-reasoning/`
**PRD Reference:** [prd.md](./prd.md)

## 1. Architecture & Component Boundaries
- **Data Model Expansion (`tradingagents/api/schemas.py`, `web/src/types/index.ts`)**:
  - Extend `CellResult` with optional agent reports: `market_report`, `fundamentals_report`, `news_report`, `sentiment_report`, `investment_debate_state`, `investment_plan`, `trader_investment_plan`, `risk_debate_state`.
- **Log Reader (`tradingagents/api/manager.py`)**:
  - Read `full_states_log_{date}.json` from `base_dir / safe_ticker / TradingAgentsStrategy_logs/` when populating `get_run_detail(run_id)`.
  - Graceful fallback when log files are absent or unreadable.
- **Frontend Presentation (`web/src/components/ResultsPanel.tsx`)**:
  - Tabbed reasoning modal supporting PM decision, Market, Fundamentals, News, Research Debate, Risk Debate, and Reflection.
  - Dynamically display only populated agent outputs.
