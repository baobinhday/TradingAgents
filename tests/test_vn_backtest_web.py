"""Unit tests for Vietnam market backtesting, date window validation, CLI runner, and Web API."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from cli.main import app
from tradingagents.api.app import app as fastapi_app
from tradingagents.api.manager import BacktestManager
from tradingagents.api.schemas import BacktestRunRequest
from tradingagents.backtest import (
    get_current_date,
    run_backtest,
    validate_backtest_dates,
)
from tradingagents.default_config import DEFAULT_CONFIG

runner = CliRunner()
client = TestClient(fastapi_app)

# ==============================================================================
# 1. Date Window Validation Tests
# ==============================================================================

@pytest.mark.unit
def test_validate_backtest_dates_us_market_allows_old_dates():
    """US market allows historical dates beyond 730 days."""
    dates = ["2020-01-01", "2020-01-08"]
    config = {**DEFAULT_CONFIG, "market": "US"}
    # Should not raise
    validate_backtest_dates(dates, config)


@pytest.mark.unit
def test_validate_backtest_dates_vn_market_within_window():
    """Vietnam market allows dates within configured window (default 730 days)."""
    today_dt = datetime.strptime(get_current_date(), "%Y-%m-%d")
    recent_date = (today_dt - timedelta(days=60)).strftime("%Y-%m-%d")
    dates = [recent_date]
    config = {**DEFAULT_CONFIG, "market": "VN", "vn_data_window_days": 730}
    validate_backtest_dates(dates, config)


@pytest.mark.unit
def test_validate_backtest_dates_vn_market_rejects_out_of_window():
    """Vietnam market rejects dates older than configured window (e.g. 730 days)."""
    today_dt = datetime.strptime(get_current_date(), "%Y-%m-%d")
    old_date = (today_dt - timedelta(days=800)).strftime("%Y-%m-%d")
    dates = [old_date]
    config = {**DEFAULT_CONFIG, "market": "VN", "vn_data_window_days": 730}

    with pytest.raises(ValueError) as excinfo:
        validate_backtest_dates(dates, config)

    msg = str(excinfo.value)
    assert old_date in msg
    assert "outside the supported Vietnam market data window" in msg
    assert "730 days" in msg
    assert "earliest supported date" in msg


@pytest.mark.unit
def test_validate_backtest_dates_vn_market_custom_window():
    """Vietnam window can be customized via config."""
    today_dt = datetime.strptime(get_current_date(), "%Y-%m-%d")
    date_100d_ago = (today_dt - timedelta(days=100)).strftime("%Y-%m-%d")
    dates = [date_100d_ago]

    # Custom window of 90 days rejects 100 days ago
    config = {**DEFAULT_CONFIG, "market": "VN", "vn_data_window_days": 90}
    with pytest.raises(ValueError) as excinfo:
        validate_backtest_dates(dates, config)
    assert "90 days" in str(excinfo.value)


# ==============================================================================
# 2. Backtest Engine & CLI Runner Tests
# ==============================================================================

@pytest.mark.unit
def test_run_backtest_rejects_out_of_window_vn_dates(tmp_path):
    today_dt = datetime.strptime(get_current_date(), "%Y-%m-%d")
    old_date = (today_dt - timedelta(days=850)).strftime("%Y-%m-%d")
    config = {**DEFAULT_CONFIG, "market": "VN", "results_dir": str(tmp_path)}

    with pytest.raises(ValueError) as excinfo:
        run_backtest(["VNM"], [old_date], config)
    assert "outside the supported Vietnam market data window" in str(excinfo.value)


@pytest.mark.unit
def test_cli_backtest_market_vn_rejects_out_of_window():
    """CLI backtest with --market VN and out-of-range dates exits with code 1."""
    today_dt = datetime.strptime(get_current_date(), "%Y-%m-%d")
    old_start = (today_dt - timedelta(days=850)).strftime("%Y-%m-%d")
    old_end = (today_dt - timedelta(days=840)).strftime("%Y-%m-%d")

    res = runner.invoke(
        app,
        ["backtest", "VNM", "--start", old_start, "--end", old_end, "--market", "VN"],
    )
    assert res.exit_code == 1
    assert "outside the supported Vietnam market data window" in res.output


# ==============================================================================
# 3. BacktestManager & API Endpoint Tests
# ==============================================================================

@pytest.mark.unit
def test_backtest_manager_rejects_out_of_window_vn():
    mgr = BacktestManager()
    today_dt = datetime.strptime(get_current_date(), "%Y-%m-%d")
    old_start = (today_dt - timedelta(days=900)).strftime("%Y-%m-%d")
    old_end = (today_dt - timedelta(days=890)).strftime("%Y-%m-%d")

    req = BacktestRunRequest(
        tickers=["VNM"],
        start_date=old_start,
        end_date=old_end,
        every_n_days=7,
        market="VN",
    )
    with pytest.raises(ValueError) as excinfo:
        mgr.start_run(req)
    assert "outside the supported Vietnam market data window" in str(excinfo.value)


@pytest.mark.unit
def test_api_config_endpoint_returns_vietnam_support():
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "VN" in data.get("available_markets", [])
    default_cfg = data.get("default_config", {})
    assert default_cfg.get("vn_data_window_days") == 730
    assert "vn_data_vendors" in default_cfg


@pytest.mark.unit
def test_api_backtest_run_endpoint_validates_vn_window():
    today_dt = datetime.strptime(get_current_date(), "%Y-%m-%d")
    old_start = (today_dt - timedelta(days=900)).strftime("%Y-%m-%d")
    old_end = (today_dt - timedelta(days=890)).strftime("%Y-%m-%d")

    payload = {
        "tickers": ["VNM"],
        "start_date": old_start,
        "end_date": old_end,
        "every_n_days": 7,
        "market": "VN",
    }
    res = client.post("/api/backtest/run", json=payload)
    assert res.status_code == 400
    assert "outside the supported Vietnam market data window" in res.json().get("detail", "")
