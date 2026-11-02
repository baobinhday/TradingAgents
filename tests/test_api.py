import pytest
from fastapi.testclient import TestClient

from tradingagents.api.app import app
from tradingagents.api.manager import backtest_manager


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.unit
def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.unit
def test_get_config(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "default_config" in data
    assert "supported_providers" in data
    assert "available_analysts" in data
    assert "openai" in data["supported_providers"]
    assert any(a["id"] == "market" for a in data["available_analysts"])


@pytest.mark.unit
def test_backtest_run_validation(client):
    # Empty tickers
    response = client.post(
        "/api/backtest/run",
        json={
            "tickers": [],
            "start_date": "2026-08-01",
            "end_date": "2026-08-10",
        },
    )
    assert response.status_code == 400
    assert "ticker" in response.json()["detail"].lower()

    # Invalid dates (end before start)
    response = client.post(
        "/api/backtest/run",
        json={
            "tickers": ["NVDA"],
            "start_date": "2026-08-10",
            "end_date": "2026-08-01",
        },
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_backtest_analyst_normalization(monkeypatch):
    from unittest.mock import MagicMock

    from tradingagents.api.schemas import BacktestRunRequest

    mock_run_backtest = MagicMock()
    mock_run_backtest.return_value = MagicMock(cells_run=1, skipped=0, failures=[], settlement_failures=[], log_path="fake")
    monkeypatch.setattr("tradingagents.api.manager.run_backtest", mock_run_backtest)
    monkeypatch.setattr("tradingagents.api.manager.summarize", lambda res: MagicMock(resolved=1, pending=0, unscored=0, holding="5d", by_rating={}, render=lambda: "ok"))

    backtest_manager.status = "idle"
    req = BacktestRunRequest(
        tickers=["NVDA"],
        start_date="2026-08-01",
        end_date="2026-08-01",
        selected_analysts=["sentiment", "market"],
    )
    run_id, total = backtest_manager.start_run(req)
    assert total == 1
    # Wait briefly for background thread
    if backtest_manager.active_thread:
        backtest_manager.active_thread.join(timeout=2.0)

    assert mock_run_backtest.called
    called_analysts = mock_run_backtest.call_args[1]["selected_analysts"]
    assert "social" in called_analysts
    assert "sentiment" not in called_analysts


@pytest.mark.unit
def test_backtest_stop_when_idle(client):
    backtest_manager.status = "idle"
    response = client.post("/api/backtest/stop")
    assert response.status_code == 400


@pytest.mark.unit
def test_list_runs(client, tmp_path, monkeypatch):
    backtest_dir = tmp_path / "backtest"
    backtest_dir.mkdir(parents=True)
    run_dir = backtest_dir / "20260901_120000"
    run_dir.mkdir()
    (run_dir / "trading_memory.md").write_text("# Memory Log\n", encoding="utf-8")

    from tradingagents.default_config import DEFAULT_CONFIG

    monkeypatch.setitem(DEFAULT_CONFIG, "results_dir", str(tmp_path))

    response = client.get("/api/backtest/runs")
    assert response.status_code == 200
    runs = response.json()
    assert len(runs) >= 1
    assert runs[0]["run_id"] == "20260901_120000"
    assert runs[0]["has_log"] is True


@pytest.mark.unit
def test_get_run_detail_not_found(client):
    response = client.get("/api/backtest/runs/non_existent_run_9999")
    assert response.status_code == 404


@pytest.mark.unit
def test_static_index_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "TradingAgents" in response.text


@pytest.mark.unit
def test_get_provider_models(client):
    response = client.get("/api/config/models?provider=openai")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert "default_deep" in data
    assert "default_quick" in data
    assert len(data["deep_models"]) > 0
    assert len(data["quick_models"]) > 0


