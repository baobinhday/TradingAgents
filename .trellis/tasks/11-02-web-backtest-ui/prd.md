# PRD: Web UI for Configuration & Backtesting

## 1. Goal & Overview
Provide an intuitive, modern, and responsive web-based user interface to configure parameters, launch and monitor backtests in real-time, and inspect backtest results and historical runs for the TradingAgents framework.

## 2. Technology Stack
- **Frontend**: Vite + React (TypeScript), Tailwind CSS, shadcn/ui components, Lucide icons, Recharts (for performance charts).
- **Backend**: FastAPI + Uvicorn (Python 3.11+), Server-Sent Events (SSE) for real-time progress streaming.
- **Integration**: Direct Python invocation of `tradingagents.backtest.run_backtest`, `summarize`, and `DEFAULT_CONFIG`.

## 3. Features & Scope
### 3.1 Configuration & Setup
- **Ticker & Date Configuration**:
  - Comma-separated ticker input with common presets (e.g., tech giants, indices).
  - Date range selector (Start Date, End Date) with step interval (`every_n_days`).
  - Asset type selection: `stock` or `crypto`.
- **Analyst Team Selection**:
  - Checkboxes for `market`, `sentiment` (social), `news`, `fundamentals`.
- **Model & Agent Settings**:
  - LLM Provider dropdown (OpenAI, Gemini, Anthropic, Bedrock, etc.).
  - Quick-think and Deep-think model selection.
  - Debate & risk rounds configuration (`max_debate_rounds`, `max_risk_discuss_rounds`).
  - Benchmark ticker (default `SPY`).

### 3.2 Live Execution & Monitoring
- **Trigger & Control**:
  - Start Backtest button with validation.
  - Cancel / Stop active run button.
- **Real-Time Progress**:
  - Progress bar showing completed cells vs total cells (`[done/total]`).
  - Current processing indicator (`ticker`, `date`).
  - Live log console streaming events via SSE.

### 3.3 Results & Analytics Dashboard
- **Summary Cards**:
  - Resolved Cells, Pending Cells, Unscored Cells.
  - Overall Hit Rate (% correct direction).
  - Mean Alpha vs Benchmark.
- **Breakdown by Rating**:
  - Table / visual cards for Buy, Overweight, Hold, Underweight, Sell (count, hit rate, mean alpha).
- **Cell Details Table**:
  - Detailed list of analyzed cells: Ticker, Date, Rating, Realized Alpha, Status, Errors (if any).
  - Search and filter by ticker or rating.
- **Run History**:
  - List of past runs from `results/backtest/`.
  - Ability to load, view, or resume earlier runs (`--run-id`).

## 4. Acceptance Criteria
- [x] Backend FastAPI service runs reliably, serving endpoints for config, running backtests, SSE streaming, and fetching run history.
- [x] Frontend built with Vite, React, Tailwind CSS, and shadcn/ui components with a clean dark/light UI.
- [x] User can configure all backtest parameters via UI and initiate a backtest.
- [x] Live progress and cell updates stream in real-time without UI lag or disconnection.
- [x] Completed runs display accurate summary metrics (Hit Rate, Mean Alpha, rating distributions) matching `cli.main:backtest`.
- [x] User can view past backtest runs and inspect detailed results per cell.
- [x] Comprehensive error handling when external APIs fail or invalid input is provided.
