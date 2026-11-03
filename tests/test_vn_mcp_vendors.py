"""Comprehensive tests for AlgoLab and SSI MCP vendors, adapters, fallback, and co-sourcing."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.dataflows.config import run_config
from tradingagents.dataflows.errors import (
    NoMarketDataError,
    VendorNotConfiguredError,
    VendorUnavailableError,
)
from tradingagents.dataflows.router import (
    VENDOR_METHODS,
    get_closes,
    route_to_vendor,
)
from tradingagents.dataflows.vendors.algolab.client import (
    AlgoLabClient,
    get_algolab_api_key,
)
from tradingagents.dataflows.vendors.algolab.market import (
    _parse_bars as parse_algolab_bars,
    get_stock_data as get_algolab_stock_data,
)
from tradingagents.dataflows.vendors.ssi.client import (
    SSIMCPClient,
    SSITokenManager,
)
from tradingagents.dataflows.vendors.ssi.market import (
    _parse_ssi_records,
)
from tradingagents.dataflows.vendors.vn_indicators import (
    build_vn_verified_market_snapshot,
    calculate_indicators_window,
)

# ==============================================================================
# 1. AlgoLab Client & Auth Tests
# ==============================================================================

@pytest.mark.unit
def test_algolab_get_api_key_from_env(monkeypatch):
    monkeypatch.setenv("ALGOLAB_API_KEY", "alm_test_secret_key_123")
    key = get_algolab_api_key()
    assert key == "alm_test_secret_key_123"


@pytest.mark.unit
def test_algolab_client_missing_key_raises_not_configured(monkeypatch):
    monkeypatch.delenv("ALGOLAB_API_KEY", raising=False)
    monkeypatch.setattr("tradingagents.dataflows.vendors.algolab.client.get_algolab_api_key", lambda: None)
    client = AlgoLabClient(api_key=None)
    with pytest.raises(VendorNotConfiguredError) as excinfo:
        client.call_rpc("tools/list")
    assert "ALGOLAB_API_KEY" in str(excinfo.value)
    assert "alm_test_secret_key_123" not in str(excinfo.value)


@pytest.mark.unit
def test_algolab_client_parses_sse_stream():
    client = AlgoLabClient(api_key="alm_fake_key")

    sse_response_text = (
        ": keep-alive\n\n"
        'data: {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "{\\"status\\": \\"success\\", \\"data\\": {\\"symbol\\": \\"VNM\\"}}"}]}}\n\n'
    )
    mock_resp = MagicMock(status_code=200, text=sse_response_text)
    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.call_tool("get_company_profile", {"symbol": "VNM"}, use_cache=False)
        assert isinstance(res, dict)
        assert res.get("status") == "success"
        assert res.get("data", {}).get("symbol") == "VNM"


@pytest.mark.unit
def test_algolab_client_ttl_caching():
    client = AlgoLabClient(api_key="alm_fake_key")
    client._cache.clear()

    sse_response_text = (
        'data: {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "{\\"data\\": 42}"}]}}\n\n'
    )
    mock_resp = MagicMock(status_code=200, text=sse_response_text)
    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        # First call hits mock network
        res1 = client.call_tool("test_tool", {"a": 1}, use_cache=True)
        assert res1 == {"data": 42}
        assert mock_post.call_count == 1

        # Second identical call uses cache
        res2 = client.call_tool("test_tool", {"a": 1}, use_cache=True)
        assert res2 == {"data": 42}
        assert mock_post.call_count == 1


@pytest.mark.unit
def test_algolab_client_error_mappings():
    client = AlgoLabClient(api_key="alm_fake_key")

    # 401 Unauthorized
    with patch("httpx.Client.post", return_value=MagicMock(status_code=401)):
        with pytest.raises(VendorUnavailableError) as excinfo:
            client.call_rpc("tools/list")
        assert "authentication" in str(excinfo.value).lower()

    # 429 Rate Limit
    with patch("httpx.Client.post", return_value=MagicMock(status_code=429)):
        with pytest.raises(VendorUnavailableError) as excinfo:
            client.call_rpc("tools/list")
        assert "rate limit" in str(excinfo.value).lower()

    # Symbol Not Found inside payload
    err_sse = (
        'data: {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "{\\"status\\": \\"error\\", \\"error\\": {\\"code\\": \\"SYMBOL_NOT_FOUND\\", \\"message\\": \\"Symbol XYZ not found\\"}}"}]}}\n\n'
    )
    with patch("httpx.Client.post", return_value=MagicMock(status_code=200, text=err_sse)):
        with pytest.raises(NoMarketDataError) as excinfo:
            client.call_tool("get_price_history", {"symbol": "XYZ"}, use_cache=False)
        assert "XYZ" in excinfo.value.symbol


# ==============================================================================
# 2. SSI Client, Token Rotation & Rate Limiting Tests
# ==============================================================================

@pytest.mark.unit
def test_ssi_token_manager_reads_and_refreshes(tmp_path):
    primary_cache = tmp_path / "ssi_tokens.json"
    initial_tokens = {
        "client_id": "test_client_id_123",
        "tokens": {
            "access_token": "expired_access_token",
            "refresh_token": "valid_single_use_refresh_token",
            "expires_in": 3600,
        },
        "created_at": 1000.0,  # clearly expired
    }
    primary_cache.write_text(json.dumps(initial_tokens))

    mgr = SSITokenManager(primary_path=primary_cache, fallback_path=tmp_path / "fallback.json")

    # Mock token endpoint returning rotated tokens
    refreshed_tokens = {
        "access_token": "new_rotated_access_token",
        "refresh_token": "new_single_use_refresh_token",
        "expires_in": 2592000,
    }
    with patch("httpx.Client.post", return_value=MagicMock(status_code=200, json=lambda: refreshed_tokens)):
        tok = mgr.get_access_token(force_refresh=True)
        assert tok == "new_rotated_access_token"

        # Verify disk persistence of rotated tokens
        persisted = json.loads(primary_cache.read_text())
        assert persisted["tokens"]["access_token"] == "new_rotated_access_token"
        assert persisted["tokens"]["refresh_token"] == "new_single_use_refresh_token"


@pytest.mark.unit
def test_ssi_token_manager_invalid_grant_raises_not_configured(tmp_path):
    cache_file = tmp_path / "ssi_tokens.json"
    cache_file.write_text(json.dumps({
        "client_id": "client_abc",
        "tokens": {"access_token": "old", "refresh_token": "used_refresh_token", "expires_in": 10},
        "created_at": 0,
    }))
    mgr = SSITokenManager(primary_path=cache_file, fallback_path=tmp_path / "none.json")

    with patch("httpx.Client.post", return_value=MagicMock(status_code=400, text='{"error": "invalid_grant"}')):
        with pytest.raises(VendorNotConfiguredError) as excinfo:
            mgr.get_access_token(force_refresh=True)
        assert "invalid or revoked" in str(excinfo.value).lower()


@pytest.mark.unit
def test_ssi_client_rate_limiting():
    mgr = MagicMock()
    mgr.get_access_token.return_value = "fake_ssi_token"
    client = SSIMCPClient(token_manager=mgr)
    client._min_interval = 0.05  # fast for testing

    sse_text = 'data: {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"text": "{\\"status\\": \\"success\\"}"}]}}\n\n'
    with patch("httpx.Client.post", return_value=MagicMock(status_code=200, text=sse_text)):
        res = client.call_rpc("tools/list")
        assert res.get("result") is not None


# ==============================================================================
# 3. Market Adapters & Zero-Volume Bar Filter Tests
# ==============================================================================

@pytest.mark.unit
def test_algolab_parse_bars_filters_zero_volume_bars():
    raw_data = {
        "columns": ["t", "o", "h", "l", "c", "v", "value", "foreign_net", "foreign_net_val"],
        "rows": [
            ["2026-10-01", 50000, 51000, 49500, 50500, 100000, 5000000000, 0, 0],
            ["2026-10-02", 50500, 50500, 50500, 50500, 0, 0, 0, 0],  # zero volume unfinished bar
            ["2026-10-03", 50500, 52000, 50000, 51500, 150000, 7500000000, 0, 0],
        ],
    }
    df = parse_algolab_bars(raw_data)
    assert len(df) == 2
    assert "2026-10-02" not in df["Date"].values
    assert list(df["Date"]) == ["2026-10-01", "2026-10-03"]


@pytest.mark.unit
def test_ssi_parse_records_normalizes_dates_and_filters_zero_volume():
    records = [
        {"trading_date": "01/10/2026", "open": "50000", "high": "51000", "low": "49000", "close": "50500", "volume": "200000"},
        {"trading_date": "02/10/2026", "open": "50500", "high": "50500", "low": "50500", "close": "50500", "volume": "0"},
        {"trading_date": "03/10/2026", "open": "50500", "high": "52000", "low": "50000", "close": "51500", "volume": "300000"},
    ]
    df = _parse_ssi_records(records)
    assert len(df) == 2
    assert df["Date"].tolist() == ["2026-10-01", "2026-10-03"]
    assert df["Close"].tolist() == [50500.0, 51500.0]


@pytest.mark.unit
def test_algolab_get_stock_data_output_format():
    mock_payload = {
        "status": "success",
        "data": {
            "bars": {
                "columns": ["t", "o", "h", "l", "c", "v"],
                "rows": [["2026-10-01", 60000, 61000, 59500, 60500, 500000]],
            }
        },
    }
    with patch.object(AlgoLabClient, "call_tool", return_value=mock_payload):
        csv_out = get_algolab_stock_data("VNM", "2026-10-01", "2026-10-05")
        assert "# Stock data for VNM from 2026-10-01 to 2026-10-05" in csv_out
        assert "Date,Open,High,Low,Close,Volume" in csv_out
        assert "2026-10-01,60000,61000,59500,60500,500000" in csv_out


# ==============================================================================
# 4. Whole-Series Fallback Tests (AlgoLab -> SSI)
# ==============================================================================

@pytest.mark.unit
def test_whole_series_fallback_when_algolab_unavailable(monkeypatch):
    """When AlgoLab fails or is unavailable, SSI serves 100% of the price series."""
    ssi_csv = "# Stock data for VNM from 2026-10-01 to 2026-10-05\n# Total records: 1\n\nDate,Open,High,Low,Close,Volume\n2026-10-01,58000,59000,57500,58500,400000\n"

    def fail_algolab(*args, **kwargs):
        raise VendorUnavailableError("AlgoLab outage")

    mock_ssi = MagicMock(return_value=ssi_csv)

    monkeypatch.setitem(VENDOR_METHODS["get_stock_data"], "algolab", fail_algolab)
    monkeypatch.setitem(VENDOR_METHODS["get_stock_data"], "ssi", mock_ssi)

    with run_config({"market": "VN"}):
        res = route_to_vendor("get_stock_data", "VNM", "2026-10-01", "2026-10-05")
        assert "Stock data for VNM" in res
        assert "58500" in res
        mock_ssi.assert_called_once_with("VNM", "2026-10-01", "2026-10-05")


@pytest.mark.unit
def test_get_closes_routes_to_vn_vendors_with_fallback(monkeypatch):
    series_ssi = pd.Series([59000.0, 59500.0], index=pd.to_datetime(["2026-10-01", "2026-10-02"]))

    with (
        run_config({"market": "VN"}),
        patch("tradingagents.dataflows.router.get_algolab_closes", side_effect=VendorUnavailableError("AlgoLab 500")),
        patch("tradingagents.dataflows.router.get_ssi_closes", return_value=series_ssi) as mock_ssi,
    ):
        closes = get_closes("VNM", "2026-10-01", "2026-10-03")
        assert len(closes) == 2
        assert closes.iloc[0] == 59000.0
        mock_ssi.assert_called_once()


# ==============================================================================
# 5. Multi-Source Co-Sourcing & News Deduplication Tests
# ==============================================================================

@pytest.mark.unit
def test_news_co_sourcing_with_deduplication(monkeypatch):
    algolab_news = (
        "## News for VNM from 2026-10-01 to 2026-10-15:\n\n"
        "### Vinamilk Expansion Plan (source: AlgoLab, sentiment: Positive)\n"
        "Vinamilk announces new factory.\n"
        "Link: https://example.com/vnm-factory\n\n"
        "### Unique AlgoLab Story (source: AlgoLab)\n"
        "AlgoLab exclusive coverage.\n"
        "Link: https://example.com/algolab-exclusive\n"
    )

    ssi_news = (
        "## News for VNM from 2026-10-01 to 2026-10-15:\n\n"
        "### Vinamilk Expansion Plan (source: HOSE)\n"
        "Official HOSE announcement on factory.\n"
        "Link: https://example.com/vnm-factory\n\n"
        "### SSI Market Update on Dairy (source: SSI)\n"
        "SSI research team review.\n"
        "Link: https://example.com/ssi-dairy\n"
    )

    monkeypatch.setitem(VENDOR_METHODS["get_news"], "algolab", lambda *a, **kw: algolab_news)
    monkeypatch.setitem(VENDOR_METHODS["get_news"], "ssi", lambda *a, **kw: ssi_news)

    with run_config({"market": "VN"}):
        res = route_to_vendor("get_news", "VNM", "2026-10-01", "2026-10-15")

        assert "### [Source: AlgoLab]" in res
        assert "### [Source: SSI]" in res
        assert "Unique AlgoLab Story" in res
        assert "SSI Market Update on Dairy" in res
        # Duplicate article (https://example.com/vnm-factory) was filtered from SSI section
        ssi_section = res.split("### [Source: SSI]")[1]
        assert "https://example.com/vnm-factory" not in ssi_section


@pytest.mark.unit
def test_co_sourcing_fail_open_with_explicit_note(monkeypatch):
    algolab_fin = "## Fundamentals for VNM:\n- **P/E Ratio (TTM)**: 10.5\n- **P/B Ratio**: 3.2"

    def fail_ssi(*args, **kwargs):
        raise VendorUnavailableError("SSI Cloudflare 403")

    monkeypatch.setitem(VENDOR_METHODS["get_fundamentals"], "algolab", lambda *a, **kw: algolab_fin)
    monkeypatch.setitem(VENDOR_METHODS["get_fundamentals"], "ssi", fail_ssi)

    with run_config({"market": "VN"}):
        res = route_to_vendor("get_fundamentals", "VNM", "2026-10-15")

        # Delivers AlgoLab data
        assert "### [Source: AlgoLab]" in res
        assert "P/E Ratio (TTM)" in res
        # Includes explicit warning note about SSI failure
        assert "> [!NOTE]" in res
        assert "SSI Cloudflare 403" in res


# ==============================================================================
# 6. Technical Indicators & Verified Market Snapshot Tests
# ==============================================================================

@pytest.mark.unit
def test_calculate_indicators_window():
    dates = pd.date_range("2026-09-01", "2026-10-15", freq="D").strftime("%Y-%m-%d")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [50000.0 + i * 100 for i in range(len(dates))],
        "High": [51000.0 + i * 100 for i in range(len(dates))],
        "Low": [49000.0 + i * 100 for i in range(len(dates))],
        "Close": [50500.0 + i * 100 for i in range(len(dates))],
        "Volume": [1000000 for _ in range(len(dates))],
    })

    ind_str = calculate_indicators_window(df, "VNM", "rsi", "2026-10-15", look_back_days=10)
    assert "## rsi values from 2026-10-05 to 2026-10-15:" in ind_str
    assert "2026-10-15:" in ind_str
    assert "RSI: Measures momentum" in ind_str


@pytest.mark.unit
def test_build_vn_verified_market_snapshot():
    dates = pd.date_range("2026-09-01", "2026-10-15", freq="D").strftime("%Y-%m-%d")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [60000.0 for _ in range(len(dates))],
        "High": [61000.0 for _ in range(len(dates))],
        "Low": [59000.0 for _ in range(len(dates))],
        "Close": [60500.0 for _ in range(len(dates))],
        "Volume": [2000000 for _ in range(len(dates))],
    })

    with patch("tradingagents.dataflows.vendors.vn_indicators.get_algolab_ohlcv", return_value=df):
        snapshot = build_vn_verified_market_snapshot("VNM", "2026-10-15", look_back_days=10)
        assert "## Verified market data snapshot for VNM" in snapshot
        assert "Requested analysis date: 2026-10-15" in snapshot
        assert "| Close | 60500.00 |" in snapshot
        assert "close_50_sma" in snapshot
        assert "Recent verified closes" in snapshot


# ==============================================================================
# 7. Security: Verify Secrets Are Never Leaked
# ==============================================================================

@pytest.mark.unit
def test_secrets_never_leaked_in_exceptions_or_logs(monkeypatch, caplog):
    secret_key = "alm_super_secret_production_key_xyz987"
    monkeypatch.setenv("ALGOLAB_API_KEY", secret_key)
    client = AlgoLabClient(api_key=secret_key)

    with patch("httpx.Client.post", side_effect=Exception("HTTP connection reset")):
        with pytest.raises(VendorUnavailableError) as excinfo:
            client.call_rpc("tools/list")
        assert secret_key not in str(excinfo.value)

    # Check captured logs
    for record in caplog.records:
        assert secret_key not in record.message


# ==============================================================================
# 8. News Slicing & PageSize Verification
# ==============================================================================

@pytest.mark.unit
def test_algolab_get_global_news_handles_columnar_items():
    from tradingagents.dataflows.vendors.algolab.news import get_global_news as algolab_global_news

    mock_recap_data = {
        "status": "success",
        "data": {
            "kind": "recap",
            "items": {
                "columns": ["kind", "id", "content", "audio_url", "message_count", "published_at"],
                "rows": [
                    ["daily_recap", "1", "🌟 DAILY RECAP 🌟\n\nVN-Index up 1.5%", None, 0, "2026-11-01"],
                    ["daily_recap", "2", "🌟 MARKET WRAP 🌟\n\nBanking sector rallies", None, 0, "2026-10-31"],
                ],
            },
        },
    }

    with patch.object(AlgoLabClient, "call_tool", return_value=mock_recap_data):
        out = algolab_global_news("2026-11-01", look_back_days=7, limit=5)
        assert "Vietnam Market Recap News" in out
        assert "DAILY RECAP" in out
        assert "VN-Index up 1.5%" in out


@pytest.mark.unit
def test_ssi_get_global_news_clamps_page_size():
    from tradingagents.dataflows.vendors.ssi.news import get_global_news as ssi_global_news

    mock_news_data = {
        "status": "ok",
        "data": {
            "news": [
                {"title": "SSI Market Report", "news_source": "SSI", "short_content": "Market summary"},
            ]
        },
    }

    with patch.object(SSIMCPClient, "call_tool") as mock_call:
        mock_call.return_value = mock_news_data
        out = ssi_global_news("2026-11-01", look_back_days=7, limit=5)
        assert "Vietnam Market News" in out
        assert "SSI Market Report" in out
        # Check that pageSize passed to tool is clamped to valid SSI options (10)
        assert mock_call.call_args[0][0] == "marketdata_list_company_news"
        args = mock_call.call_args[0][1]
        assert args["pageSize"] == 10

