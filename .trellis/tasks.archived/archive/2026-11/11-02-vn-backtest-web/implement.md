# Implementation Plan: Vietnam Backtest & Web UI Integration

## Work Breakdown

### Phase 1: Core Configuration & Date Window Guard
- [x] Add `"vn_data_window_days": 730` to `tradingagents/default_config.py`.
- [x] Add `validate_backtest_dates(dates, config)` to `tradingagents/backtest.py`.
  - Validate that for `market == "VN"` (or tickers ending in `.VN`), all dates are within `vn_data_window_days` from today.
  - Call in `run_backtest` and `BacktestManager.start_run`.
- [x] Ensure `cli/main.py` backtest command respects `--market VN` and validates dates with clear error messages.

### Phase 2: Web UI Market Support
- [x] Update `web/src/types/index.ts`:
  - Add `market?: string` to `BacktestRunRequest`.
  - Add `available_markets?: string[]` to `ConfigResponse`.
- [x] Update `web/src/components/ConfigPanel.tsx`:
  - Add Market selector (`US` vs `Vietnam`).
  - Add Vietnamese ticker presets (`VN30 Bluechips`, `Banking`, `Securities & Tech`, `Real Estate & Steel`).
  - Restrict date picker: set `min={earliestVnDate}` and `max={today}` for Vietnam.
  - Set benchmark default to `VNINDEX`.
  - Validate date window and display clear inline error if start date is outside the 730-day window.
- [x] Rebuild Web UI (`npm run build` in `web/`).

### Phase 3: Testing & Verification
- [x] Unit tests in `tests/test_vn_backtest_web.py`:
  - Test `validate_backtest_dates` allows valid dates within 730 days and raises `ValueError` for out-of-range dates.
  - Test `BacktestManager.start_run` rejects out-of-window dates for `market="VN"`.
  - Test `run_backtest` with `market="VN"` creates runs and settles alpha vs `VNINDEX`.
  - Test Web API `/api/config` and `/api/backtest/run` handle `market="VN"`.
- [x] Run full test suite (`uv run pytest`) and linting (`uv run ruff check`).
