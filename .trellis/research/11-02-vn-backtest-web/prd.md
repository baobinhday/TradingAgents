# PRD: Vietnam Backtest and Web UI Integration

**Status:** Completed
<!-- Lifecycle: Draft -> In Review -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-02-vn-backtest-web/`

## Goal

Support Vietnam runs in backtest simulation, CLI runner, and Web console with point-in-time guards and a configurable historical data window, default 730 days.

## Confirmed Spike Insights

- The Vietnam data window is configurable, default 730 days (SSI's limit). AlgoLab, the primary price source, reaches further, and raising the window applies to prices and VN-Index only. Non-price sources keep their own limits and report uncovered windows as unavailable. Dates outside the configured window are rejected with a clear error.
- News is limited to the last 6 months.
- Benchmark: VNINDEX (or VN30).

## Requirements

1. **CLI & API Market Parameter**:
   - Add `--market [US|VN]` flag to CLI backtest commands.
   - Add `market: "US" | "VN"` field to API schemas and backtest configuration.
2. **Web UI Support**:
   - Add Market selector (`US` vs `Vietnam`) in the Web UI backtest configuration form.
   - For Vietnam market:
     * Restrict date picker to the configured data window.
     * Populate benchmark default to `VNINDEX`.
     * Preload popular Vietnamese tickers (`SSI`, `VNM`, `VCB`, `FPT`, `HPG`, `MWG`).
3. **Point-in-Time Guards in Backtesting**:
   - Enforce date window boundaries so historical simulations do not query out-of-range dates.
   - Guard against lookahead leakage when applying financial statements.

## Acceptance Criteria

- [x] Web UI displays Market selector and adjusts date constraints dynamically for Vietnam.
- [x] Backtest runner accepts `market="VN"`, ticker="VNM", and executes end-to-end without errors.
- [x] Attempting to backtest beyond the configured window shows a clear, actionable validation error in both CLI and Web UI.
- [x] SSE progress streaming and final performance reports render Vietnamese backtest results correctly.
