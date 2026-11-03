from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

from tradingagents.api.schemas import (
    BacktestRunRequest,
    BacktestSummaryResponse,
    CellResult,
    RatingScoreResponse,
    RunDetailResponse,
    RunListItem,
)
from tradingagents.backtest import (
    BacktestResult,
    iter_grid,
    run_backtest,
    summarize,
    validate_backtest_dates,
)
from tradingagents.dataflows.symbols import safe_ticker_component
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.memory import TradingMemoryLog

logger = logging.getLogger(__name__)


class StreamLogHandler(logging.Handler):
    """Logging handler that pushes log records into the backtest event stream."""

    def __init__(self, manager: BacktestManager):
        super().__init__()
        self.manager = manager

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.manager.publish_sync(
                "log",
                {
                    "timestamp": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
                    "level": record.levelname,
                    "message": msg,
                },
            )
        except Exception:
            self.handleError(record)


class BacktestManager:
    """Manages asynchronous backtest runs, cancellation, and event subscriptions."""

    def __init__(self):
        self._lock = threading.Lock()
        self.active_run_id: str | None = None
        self.active_thread: threading.Thread | None = None
        self.status: str = "idle"  # idle, running, completed, failed, stopped
        self.stop_requested = threading.Event()
        self.latest_result: BacktestResult | None = None
        self.latest_error: str | None = None
        self.latest_summary: BacktestSummaryResponse | None = None
        self.subscribers: set[asyncio.Queue] = set()
        self.log_buffer: list[dict[str, Any]] = []
        self.loop: asyncio.AbstractEventLoop | None = None

        # Setup logging intercept
        self._log_handler = StreamLogHandler(self)
        self._log_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger("tradingagents").addHandler(self._log_handler)

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def publish_sync(self, event: str, data: dict[str, Any]):
        """Publish an event to all connected SSE subscriber queues from a sync thread."""
        if not self.loop or self.loop.is_closed():
            return
        payload = {"event": event, "data": data}
        if event == "log":
            self.log_buffer.append(data)
            if len(self.log_buffer) > 200:
                self.log_buffer.pop(0)

        for q in list(self.subscribers):
            self.loop.call_soon_threadsafe(q.put_nowait, payload)

    async def subscribe(self) -> AsyncGenerator[dict[str, Any], None]:
        """Async generator yielding events to an SSE endpoint."""
        q: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(q)
        try:
            # Yield initial status and cached logs
            yield {
                "event": "status",
                "data": {
                    "run_id": self.active_run_id,
                    "status": self.status,
                    "recent_logs": self.log_buffer[-50:],
                },
            }
            while True:
                msg = await q.get()
                yield msg
        finally:
            self.subscribers.discard(q)

    def start_run(self, req: BacktestRunRequest) -> tuple[str, int]:
        """Start a new backtest run in a background thread."""
        with self._lock:
            # Sync status if active_thread is finished
            if self.active_thread and not self.active_thread.is_alive() and self.status == "running":
                self.status = "idle"

            if self.status == "running":
                raise RuntimeError("A backtest is already running. Please stop it or wait for completion.")

            dates = iter_grid(req.start_date, req.end_date, req.every_n_days)
            tickers = [t.strip().upper() for t in req.tickers if t.strip()]
            if not tickers:
                raise ValueError("At least one ticker must be specified")
            if not dates:
                raise ValueError(f"No dates generated between {req.start_date} and {req.end_date}")

            total_cells = len(tickers) * len(dates)
            run_id = req.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")

            # Merge config overrides and validate date boundaries
            run_config = DEFAULT_CONFIG.copy()
            run_config.update(req.config_overrides)
            if req.market:
                run_config["market"] = req.market.strip().upper()

            validate_backtest_dates(dates, run_config)

            self.active_run_id = run_id
            self.status = "running"
            self.stop_requested.clear()
            self.latest_result = None
            self.latest_error = None
            self.latest_summary = None
            self.log_buffer.clear()

            # Normalize analyst keys: "sentiment" is the UX display name, core key is "social"
            clean_analysts = [
                "social" if a.strip().lower() == "sentiment" else a.strip().lower()
                for a in req.selected_analysts
            ]
            if req.asset_type.lower() == "crypto":
                clean_analysts = [a for a in clean_analysts if a != "fundamentals"]

            def target():
                this_run_id = run_id
                try:
                    self.publish_sync(
                        "start",
                        {
                            "run_id": this_run_id,
                            "tickers": tickers,
                            "dates": dates,
                            "total_cells": total_cells,
                            "asset_type": req.asset_type,
                        },
                    )

                    def progress(done: int, total: int, ticker: str, date: str):
                        if self.stop_requested.is_set() or self.active_run_id != this_run_id:
                            raise InterruptedError("Backtest stopped by user.")
                        percent = round((done / total) * 100, 1)
                        self.publish_sync(
                            "progress",
                            {
                                "done": done,
                                "total": total,
                                "percent": percent,
                                "ticker": ticker,
                                "date": date,
                            },
                        )

                    result = run_backtest(
                        tickers=tickers,
                        dates=dates,
                        config=run_config,
                        asset_type=req.asset_type,
                        portfolio=req.portfolio,
                        selected_analysts=clean_analysts,
                        run_id=this_run_id,
                        progress=progress,
                    )

                    # If stopped or replaced by another run, exit early
                    if self.stop_requested.is_set() or self.active_run_id != this_run_id:
                        return

                    summary_raw = summarize(result)
                    summary_resp = self._format_summary(summary_raw)

                    with self._lock:
                        if self.active_run_id == this_run_id:
                            self.latest_result = result
                            self.latest_summary = summary_resp
                            self.status = "completed"

                    self.publish_sync(
                        "complete",
                        {
                            "run_id": this_run_id,
                            "cells_run": result.cells_run,
                            "skipped": result.skipped,
                            "summary": summary_resp.model_dump(),
                            "failures": result.failures,
                            "settlement_failures": result.settlement_failures,
                        },
                    )

                except InterruptedError as exc:
                    with self._lock:
                        if self.active_run_id == this_run_id:
                            self.status = "stopped"
                            self.latest_error = str(exc)
                    self.publish_sync("stopped", {"run_id": this_run_id, "message": str(exc)})
                except Exception as exc:
                    logger.exception("Backtest run %s failed: %s", this_run_id, exc)
                    with self._lock:
                        if self.active_run_id == this_run_id:
                            self.status = "failed"
                            self.latest_error = str(exc)
                    self.publish_sync("error", {"run_id": this_run_id, "error": str(exc)})

            self.active_thread = threading.Thread(target=target, daemon=True)
            self.active_thread.start()
            return run_id, total_cells

    def stop_run(self, run_id: str | None = None) -> bool:
        """Signal the running backtest to halt immediately."""
        with self._lock:
            if self.status != "running":
                return False
            if run_id and self.active_run_id != run_id:
                return False
            self.stop_requested.set()
            self.status = "stopped"
            self.latest_error = "Backtest stopped by user."
            stopped_id = self.active_run_id or run_id or ""
            self.publish_sync(
                "stopped",
                {"run_id": stopped_id, "message": "Backtest stopped by user."},
            )
            return True

    def reset_state(self) -> None:
        """Force reset the backtest manager to idle state."""
        with self._lock:
            self.stop_requested.set()
            self.status = "idle"
            self.active_run_id = None
            self.latest_error = None
            self.publish_sync("reset", {"status": "idle"})

    def _format_summary(self, summary_raw) -> BacktestSummaryResponse:
        by_rating = {}
        for rating, score in summary_raw.by_rating.items():
            by_rating[rating] = RatingScoreResponse(
                count=score.count,
                hit_rate=score.hit_rate,
                mean_alpha=score.mean_alpha,
            )
        return BacktestSummaryResponse(
            resolved=summary_raw.resolved,
            pending=summary_raw.pending,
            unscored=summary_raw.unscored,
            holding=summary_raw.holding,
            by_rating=by_rating,
            rendered_text=summary_raw.render(),
        )

    def list_runs(self, results_dir: str | Path | None = None) -> list[RunListItem]:
        """List historical backtest runs stored in results_dir/backtest."""
        base_dir = Path(results_dir or DEFAULT_CONFIG["results_dir"]) / "backtest"
        if not base_dir.exists():
            return []

        runs = []
        for run_path in sorted(base_dir.iterdir(), key=lambda p: p.name, reverse=True):
            if not run_path.is_dir():
                continue
            run_id = run_path.name
            log_file = run_path / "trading_memory.md"
            has_log = log_file.is_file()
            cell_count = 0
            resolved_count = 0
            summary_resp = None

            if has_log:
                try:
                    entries = TradingMemoryLog({"memory_log_path": str(log_file)}).load_entries()
                    cell_count = len(entries)
                    summary_raw = summarize(log_file)
                    summary_resp = self._format_summary(summary_raw)
                    resolved_count = summary_resp.resolved
                except Exception:
                    pass

            created_time = datetime.fromtimestamp(run_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            runs.append(
                RunListItem(
                    run_id=run_id,
                    created_at=created_time,
                    has_log=has_log,
                    cell_count=cell_count,
                    resolved_count=resolved_count,
                    summary=summary_resp,
                )
            )
        return runs

    def get_run_detail(self, run_id: str, results_dir: str | Path | None = None) -> RunDetailResponse | None:
        """Get detailed breakdown of a specific backtest run."""
        base_dir = Path(results_dir or DEFAULT_CONFIG["results_dir"]) / "backtest" / run_id
        if not base_dir.exists() or not base_dir.is_dir():
            return None

        log_file = base_dir / "trading_memory.md"
        summary_resp = None
        cells = []

        if log_file.is_file():
            try:
                entries = TradingMemoryLog({"memory_log_path": str(log_file)}).load_entries()
                summary_raw = summarize(log_file)
                summary_resp = self._format_summary(summary_raw)
                for e in entries:
                    ticker = e.get("ticker", "")
                    date = e.get("date", "")
                    state_log: dict[str, Any] = {}
                    if ticker and date:
                        safe_ticker = safe_ticker_component(ticker)
                        state_file = (
                            base_dir
                            / safe_ticker
                            / "TradingAgentsStrategy_logs"
                            / f"full_states_log_{date}.json"
                        )
                        if state_file.is_file():
                            try:
                                with open(state_file, encoding="utf-8") as sf:
                                    state_log = json.load(sf)
                            except Exception as state_err:
                                logger.debug(
                                    "Could not read full state log for %s on %s: %s",
                                    ticker,
                                    date,
                                    state_err,
                                )

                    cells.append(
                        CellResult(
                            ticker=ticker,
                            date=date,
                            rating=e.get("rating"),
                            alpha=e.get("alpha"),
                            holding=e.get("holding"),
                            pending=bool(e.get("pending", False)),
                            decision=e.get("decision"),
                            reflection=e.get("reflection"),
                            market_report=state_log.get("market_report"),
                            fundamentals_report=state_log.get("fundamentals_report"),
                            news_report=state_log.get("news_report"),
                            sentiment_report=state_log.get("sentiment_report"),
                            investment_debate_state=state_log.get("investment_debate_state"),
                            investment_plan=state_log.get("investment_plan"),
                            trader_investment_plan=state_log.get("trader_investment_plan"),
                            risk_debate_state=state_log.get("risk_debate_state"),
                        )
                    )
            except Exception as exc:
                logger.warning("Error reading run detail for %s: %s", run_id, exc)

        status = "completed" if summary_resp else ("running" if run_id == self.active_run_id else "unknown")
        failures = self.latest_result.failures if (self.latest_result and self.active_run_id == run_id) else []
        settlement_failures = (
            self.latest_result.settlement_failures if (self.latest_result and self.active_run_id == run_id) else []
        )

        return RunDetailResponse(
            run_id=run_id,
            status=status,
            cells_run=len(cells),
            summary=summary_resp,
            cells=cells,
            failures=failures,
            settlement_failures=settlement_failures,
        )


# Global singleton manager instance
backtest_manager = BacktestManager()
