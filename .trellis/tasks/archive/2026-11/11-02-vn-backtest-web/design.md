# Technical Design: Vietnam Backtest & Web UI Integration

## 1. Architecture & Design Decisions

### 1.1 Configurable Historical Window & Date Guards
- **Spike Insight**: SSI MCP enforces a maximum historical range of 730 days (~2 years). While AlgoLab price feeds can reach further back, non-price tools (news, financials, ratios) and SSI are constrained.
- **Config Key**: `"vn_data_window_days": 730` in `DEFAULT_CONFIG`.
- **Validation**:
  - `validate_backtest_dates(dates, config)`: Rejects any date earlier than `today - vn_data_window_days` with a descriptive, actionable error message.
  - Triggered in both sync entry points (`cli/main.py:backtest`, `tradingagents/backtest.py:run_backtest`) and async API entry point (`BacktestManager.start_run`), preventing invalid sweep initiation.

### 1.2 Benchmark Alignment
- For `market="VN"`, decisions evaluate alpha against `VNINDEX` (regional benchmark) resolved deterministically in `tradingagents/memory/settlement.py:resolve_benchmark`.

### 1.3 Web UI Extensions
- **Market Selection**:
  - Add market selector (`US` vs `Vietnam (VN)`) in `ConfigPanel.tsx`.
  - When switching to Vietnam:
    - Preload VN30 / popular tickers (`VNM, FPT, HPG, VCB, SSI, MWG`).
    - Constrain start/end date pickers (`min={earliestVnDate}`, `max={today}`).
    - Pass `market: "VN"` in `BacktestRunRequest` and `config_overrides`.
- **Live Monitor & Results**:
  - SSE progress streaming (`/api/backtest/events`) streams cell execution (`ticker`, `date`, `done`, `total`, `percent`).
  - `ResultsPanel.tsx` and `LiveMonitor.tsx` display ratings, hit rate, and alpha vs `VNINDEX`.

### 1.4 Point-in-Time Integrity
- Runs inside the backtest sweep respect simulated statutory reporting lag for financial statements and profile withholding established in `vn_lag.py` and `date_window.py`.
