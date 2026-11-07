# PRD: Show Comprehensive Multi-Agent Reasoning in ResultsPanel

**Status:** Completed
<!-- Lifecycle: Draft -> In Review -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-03-show-multi-agent-reasoning/`

## Goal

Expand the backtest cell detail API and ResultsPanel modal in the web interface to display full multi-agent reasoning: Market Analyst, Fundamentals Analyst, News & Sentiment Analyst, Research Debate (Bull vs Bear) & Investment Plan, Risk Management Debate, Portfolio Manager Decision & Thesis, and Settlement Reflection.

## Requirements

### Backend (`tradingagents/api`)
1. In `tradingagents/api/schemas.py`, extend `CellResult` with optional agent reporting fields:
   - `market_report: str | None = None`
   - `fundamentals_report: str | None = None`
   - `news_report: str | None = None`
   - `sentiment_report: str | None = None`
   - `investment_debate_state: dict[str, Any] | None = None`
   - `investment_plan: str | None = None`
   - `trader_investment_plan: str | None = None`
   - `risk_debate_state: dict[str, Any] | None = None`
2. In `tradingagents/api/manager.py`:
   - When loading cells for `get_run_detail(run_id)`, look up the corresponding `full_states_log_{date}.json` under `base_dir / safe_ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{date}.json"`.
   - If present, populate the above report fields into `CellResult`.
   - Maintain robust error handling if the file does not exist, is partial, or fails to parse.

### Frontend (`web/src`)
1. In `web/src/types/index.ts`, update `CellResult` interface to include the new fields.
2. In `web/src/components/ResultsPanel.tsx`:
   - Redesign the Reasoning Modal into a multi-tab or sectioned view (tabs: Decision & PM, Market, Fundamentals, News & Sentiment, Research Debate, Risk Debate, Settlement Reflection).
   - Only activate/render tabs for agents that produced output in that run cell.
   - Clean markdown formatting and responsive scrollable container.
3. Build the frontend (`npm run build`) and update bundle references if necessary.

## Acceptance Criteria

- [x] `CellResult` schema in backend and frontend includes reports and debate state fields.
- [x] `get_run_detail` successfully attaches reports from `full_states_log_*.json` if available.
- [x] ResultsPanel modal allows switching between different agent reasoning views (PM, Market, Fundamentals, News, Research Debate, Risk Debate, Reflection).
- [x] Backend tests pass without regression (1503 unit tests passed).
- [x] Frontend builds cleanly with `npm run build`.
