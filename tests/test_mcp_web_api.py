from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tradingagents.api.app import app
from tradingagents.dataflows.vendors.algolab.client import AlgoLabClient
from tradingagents.dataflows.vendors.ssi.client import SSIMCPClient, SSITokenManager


@pytest.fixture
def client():
    return TestClient(app)


def test_get_mcp_status(client, monkeypatch):
    monkeypatch.setenv("ALGOLAB_API_KEY", "alm_mock_api_key_12345")
    with (
        patch.object(AlgoLabClient, "call_rpc", return_value={"result": {"tools": [{"name": "get_quotes"}]}}),
        patch.object(SSIMCPClient, "call_rpc", return_value={"result": {"tools": [{"name": "marketdata_list_stock_daily_data"}]}}),
        patch.object(SSITokenManager, "_read_cache", return_value={"client_id": "test-client", "tokens": {"access_token": "mock-token", "expires_in": 3600}}),
    ):
        res = client.get("/api/mcp/status")
        assert res.status_code == 200
        data = res.json()
        assert data["algolab"]["configured"] is True
        assert data["algolab"]["connected"] is True
        assert data["algolab"]["api_key_masked"] == "alm_...2345"
        assert data["ssi"]["configured"] is True
        assert data["ssi"]["connected"] is True
        assert data["ssi"]["client_id"] == "test-client"


def test_submit_algolab_key(client, tmp_path, monkeypatch):
    test_env = tmp_path / ".env"
    monkeypatch.setattr("tradingagents.api.routes.mcp.Path", lambda p: test_env if p == ".env" else Path(p))

    with patch.object(AlgoLabClient, "call_rpc", return_value={"result": {"tools": [1, 2, 3]}}):
        res = client.post("/api/mcp/algolab/key", json={"api_key": "alm_new_test_key_8888"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "alm_new_test_key_8888" in test_env.read_text()


def test_submit_ssi_tokens(client, tmp_path, monkeypatch):
    test_cache = tmp_path / "ssi_tokens.json"
    monkeypatch.setattr("tradingagents.api.routes.mcp.PRIMARY_TOKEN_FILE", test_cache)

    res = client.post(
        "/api/mcp/ssi/tokens",
        json={
            "access_token": "manual-access-token-999",
            "refresh_token": "manual-refresh-token-999",
            "client_id": "manual-client-id",
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_start_ssi_auth(client):
    with patch("tradingagents.api.routes.mcp._register_ssi_client", return_value="dcr-mock-client-123"):
        res = client.post("/api/mcp/ssi/auth/start", json={"redirect_uri": "http://localhost:8000/api/mcp/ssi/callback"})
        assert res.status_code == 200
        data = res.json()
        assert "auth_url" in data
        assert "state" in data
        assert "client_id" in data
        assert "https://mcp.ssi.com.vn/oauth/authorize" in data["auth_url"]
        assert "dcr-mock-client-123" in data["auth_url"]


def test_ssi_oauth_callback(client, tmp_path, monkeypatch):
    from tradingagents.api.routes.mcp import _pending_ssi_auth

    test_cache = tmp_path / "ssi_tokens.json"
    monkeypatch.setattr("tradingagents.api.routes.mcp.PRIMARY_TOKEN_FILE", test_cache)

    mock_state = "test_oauth_state_123"
    _pending_ssi_auth[mock_state] = {
        "verifier": "test_verifier",
        "client_id": "test_client_id",
        "redirect_uri": "http://localhost:8000/api/mcp/ssi/callback",
        "timestamp": 1000000,
    }

    mock_token_resp = MagicMock(status_code=200)
    mock_token_resp.json.return_value = {
        "access_token": "mock-callback-access-token",
        "refresh_token": "mock-callback-refresh-token",
        "expires_in": 3600,
    }

    with patch("httpx.post", return_value=mock_token_resp):
        res = client.get(f"/api/mcp/ssi/callback?code=mock_auth_code&state={mock_state}")
        assert res.status_code == 200
        assert "SSI MCP Authenticated" in res.text
        assert "SSI_AUTH_SUCCESS" in res.text


def test_mcp_test_endpoints(client):
    with patch.object(AlgoLabClient, "call_rpc", return_value={"result": {"tools": [{"name": "t1"}]}}), \
         patch.object(AlgoLabClient, "call_tool", return_value={"meta": {"quota": {"used": 50, "limit": 1000}}}):
        res = client.post("/api/mcp/algolab/test")
        assert res.status_code == 200
        assert res.json()["tools_count"] == 1
        assert res.json()["quota"] == {"used": 50, "limit": 1000}

    with patch.object(SSITokenManager, "_read_cache", return_value={"tokens": {"access_token": "tok"}}), \
         patch.object(SSIMCPClient, "call_rpc", return_value={"result": {"tools": [1, 2, 3, 4]}}):
        res = client.post("/api/mcp/ssi/test")
        assert res.status_code == 200
        assert res.json()["tools_count"] == 4
