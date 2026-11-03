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
def test_backtest_reset(client):
    backtest_manager.status = "stopped"
    backtest_manager.active_run_id = "test_run_123"
    response = client.post("/api/backtest/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "idle"
    assert backtest_manager.status == "idle"
    assert backtest_manager.active_run_id is None


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
def test_get_run_detail_with_full_state_log(client, tmp_path, monkeypatch):
    import json

    from tradingagents.default_config import DEFAULT_CONFIG

    monkeypatch.setitem(DEFAULT_CONFIG, "results_dir", str(tmp_path))

    backtest_dir = tmp_path / "backtest"
    run_dir = backtest_dir / "run_full_state"
    run_dir.mkdir(parents=True)

    log_entry = (
        "[2026-10-04 | FPT | Buy | pending]\n\n"
        "DECISION:\nBuy 100 shares\n\n<!-- ENTRY_END -->\n\n"
    )
    (run_dir / "trading_memory.md").write_text(log_entry, encoding="utf-8")

    logs_dir = run_dir / "FPT" / "TradingAgentsStrategy_logs"
    logs_dir.mkdir(parents=True)
    full_state = {
        "market_report": "Technical momentum is strong",
        "fundamentals_report": "Revenue up 15%",
        "news_report": "Positive market sentiment",
        "sentiment_report": "Bullish social tone",
        "investment_debate_state": {"history": "Bull and Bear debate text"},
        "investment_plan": "Accumulate on dips",
        "trader_investment_plan": "Limit order at 62.0",
        "risk_debate_state": {"history": "Aggressive and Conservative debate"},
    }
    (logs_dir / "full_states_log_2026-10-04.json").write_text(
        json.dumps(full_state), encoding="utf-8"
    )

    response = client.get("/api/backtest/runs/run_full_state")
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "run_full_state"
    assert len(data["cells"]) == 1
    cell = data["cells"][0]
    assert cell["ticker"] == "FPT"
    assert cell["date"] == "2026-10-04"
    assert cell["market_report"] == "Technical momentum is strong"
    assert cell["fundamentals_report"] == "Revenue up 15%"
    assert cell["news_report"] == "Positive market sentiment"
    assert cell["sentiment_report"] == "Bullish social tone"
    assert cell["investment_debate_state"]["history"] == "Bull and Bear debate text"
    assert cell["investment_plan"] == "Accumulate on dips"
    assert cell["trader_investment_plan"] == "Limit order at 62.0"
    assert cell["risk_debate_state"]["history"] == "Aggressive and Conservative debate"


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


@pytest.mark.unit
def test_get_openai_compatible_models_api(client, monkeypatch):
    from unittest.mock import MagicMock

    import requests

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"id": "vllm-model-1"}, {"id": "vllm-model-2-8b"}]
    }
    monkeypatch.setattr(requests, "get", lambda *a, **kw: mock_resp)

    response = client.get("/api/config/models?provider=openai_compatible&base_url=http://localhost:8000/v1")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai_compatible"
    assert data["is_live"] is True
    ids = [m["id"] for m in data["all_models"]]
    assert "vllm-model-1" in ids
    assert "vllm-model-2-8b" in ids



