from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from tradingagents.api.manager import backtest_manager
from tradingagents.api.schemas import (
    BacktestRunRequest,
    RunDetailResponse,
    RunListItem,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backtest", tags=["Backtest"])


@router.post("/run")
def start_backtest(req: BacktestRunRequest) -> dict[str, Any]:
    """Start a backtest sweep across specified tickers and dates."""
    try:
        run_id, total_cells = backtest_manager.start_run(req)
        return {
            "run_id": run_id,
            "total_cells": total_cells,
            "status": "running",
            "message": f"Backtest started for {len(req.tickers)} tickers across {total_cells} total cells.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to start backtest: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/events")
async def stream_events(request: Request):
    """Server-Sent Events endpoint streaming real-time backtest progress and logs."""

    async def event_generator():
        async for msg in backtest_manager.subscribe():
            if await request.is_disconnected():
                break
            yield {
                "event": msg.get("event", "message"),
                "data": json.dumps(msg.get("data", {})),
            }

    return EventSourceResponse(event_generator())


@router.post("/stop")
def stop_backtest(run_id: str | None = None) -> dict[str, Any]:
    """Halt the current active backtest run."""
    stopped = backtest_manager.stop_run(run_id)
    if not stopped:
        raise HTTPException(
            status_code=400,
            detail="No active backtest matching the criteria is currently running to stop.",
        )
    return {"status": "stopped", "message": "Backtest run stopped."}


@router.post("/reset")
def reset_backtest() -> dict[str, Any]:
    """Force reset the backtest state to idle."""
    backtest_manager.reset_state()
    return {"status": "idle", "message": "Backtest engine state reset to idle."}


@router.get("/status")
def get_current_status() -> dict[str, Any]:
    """Get the current running status and active run ID."""
    return {
        "status": backtest_manager.status,
        "active_run_id": backtest_manager.active_run_id,
        "latest_error": backtest_manager.latest_error,
        "latest_summary": backtest_manager.latest_summary.model_dump()
        if backtest_manager.latest_summary
        else None,
    }


@router.get("/runs", response_model=list[RunListItem])
def list_runs() -> list[RunListItem]:
    """List all past backtest sweeps found on disk."""
    return backtest_manager.list_runs()


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def get_run_detail(run_id: str) -> RunDetailResponse:
    """Retrieve detailed analysis cells and score summary for a specific run."""
    detail = backtest_manager.get_run_detail(run_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Backtest run '{run_id}' not found.")
    return detail
