"""Tests for Vietnam market foundation (11-02-vn-market-foundation).

Verifies:
1. Explicit market concept ('market="VN" | "US"') in configuration, API schemas, and state.
2. Symbol normalization for Vietnamese equities and indices.
3. Benchmark mapping to VNINDEX for Vietnam equities.
4. Complete elimination of direct Yahoo Finance imports outside router/yahoo vendor.
5. Strict isolation: zero Yahoo calls when market="VN".
"""

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tradingagents.agents.context import (
    _identity,
    resolve_instrument_identity,
)
from tradingagents.agents.state import AgentState
from tradingagents.agents.tools import get_verified_market_snapshot
from tradingagents.api.schemas import BacktestRunRequest, ConfigResponse
from tradingagents.dataflows.config import run_config
from tradingagents.dataflows.router import get_closes, route_to_vendor
from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.default_config import DEFAULT_CONFIG, build_default_config
from tradingagents.graph.propagation import Propagator
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.memory.settlement import resolve_benchmark

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# 1. Market Configuration & Schemas
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_default_config_has_market_and_vn_vendors():
    cfg = build_default_config()
    assert cfg.get("market") == "US"
    assert "vn_data_vendors" in cfg
    assert cfg["vn_data_vendors"]["core_stock_apis"] == "algolab,ssi"
    assert cfg["benchmark_map"].get(".VN") == "VNINDEX"


@pytest.mark.unit
def test_market_env_override(monkeypatch):
    monkeypatch.setenv("TRADINGAGENTS_MARKET", "VN")
    cfg = build_default_config()
    assert cfg["market"] == "VN"


@pytest.mark.unit
def test_api_schemas_support_market():
    # BacktestRunRequest defaults to "US"
    req_us = BacktestRunRequest(
        tickers=["AAPL"],
        start_date="2026-01-01",
        end_date="2026-01-30",
    )
    assert req_us.market == "US"

    # Explicit Vietnam market
    req_vn = BacktestRunRequest(
        tickers=["VNM", "SSI"],
        start_date="2026-01-01",
        end_date="2026-01-30",
        market="VN",
    )
    assert req_vn.market == "VN"

    # ConfigResponse lists available markets
    cfg_resp = ConfigResponse(
        default_config={},
        supported_providers=["openai"],
        provider_details=[],
        available_analysts=[],
        available_asset_types=["stock", "crypto"],
        available_markets=["US", "VN"],
    )
    assert "VN" in cfg_resp.available_markets
    assert "US" in cfg_resp.available_markets


# ---------------------------------------------------------------------------
# 2. Graph State & Propagation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_market_in_agent_state_annotations():
    assert "market" in AgentState.__annotations__


@pytest.mark.unit
def test_propagator_initial_state_propagates_market():
    prop = Propagator()
    state_us = prop.create_initial_state("AAPL", "2026-01-15")
    assert state_us["market"] == "US"

    state_vn = prop.create_initial_state("VNM", "2026-01-15", market="VN")
    assert state_vn["market"] == "VN"


@pytest.mark.unit
def test_trading_graph_create_run_state_propagates_market():
    graph = object.__new__(TradingAgentsGraph)
    graph.config = {**DEFAULT_CONFIG, "market": "VN"}
    graph.propagator = Propagator()
    graph.resolve_instrument_context = lambda t, a="stock", d=None, market=None: ""
    state = graph.create_run_state("VNM", "2026-01-15")
    assert state["market"] == "VN"


# ---------------------------------------------------------------------------
# 3. Symbol Normalization
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "raw,market,expected",
    [
        # Bare VN stocks remain clean uppercase
        ("VNM", "VN", "VNM"),
        ("vnm", "VN", "VNM"),
        ("SSI", "VN", "SSI"),
        ("VCB", "VN", "VCB"),
        ("BSR", "VN", "BSR"),
        ("QNS", "VN", "QNS"),
        ("vnindex", "VN", "VNINDEX"),
        ("VN30", "VN", "VN30"),
        # Stripping .VN suffix
        ("VNM.VN", "VN", "VNM"),
        ("vnm.vn", "VN", "VNM"),
        ("SSI.VN", None, "SSI"),  # auto-detected by .VN suffix
        # Trailing plus (CFD marker)
        ("VNM+", "VN", "VNM"),
        # US / global symbols remain standard
        ("aapl", "US", "AAPL"),
        ("XAUUSD", "US", "GC=F"),
        ("BTCUSD", "US", "BTC-USD"),
        ("EURUSD", "US", "EURUSD=X"),
        ("09992.HK", "US", "9992.HK"),
        ("600519.SH", "US", "600519.SS"),
    ],
)
def test_normalize_symbol_market_aware(raw, market, expected):
    assert normalize_symbol(raw, market=market) == expected


# ---------------------------------------------------------------------------
# 4. Benchmark Mapping & Resolution
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_resolve_benchmark_for_vietnam():
    # Implicit by market="VN"
    assert resolve_benchmark("VNM", {"market": "VN"}) == "VNINDEX"
    assert resolve_benchmark("SSI", {"market": "VN"}) == "VNINDEX"

    # Explicit .VN suffix in benchmark map
    assert resolve_benchmark("VNM.VN", {"market": "US"}) == "VNINDEX"

    # Custom benchmark_ticker overrides
    assert resolve_benchmark("VNM", {"market": "VN", "benchmark_ticker": "VN30"}) == "VN30"

    # US defaults to SPY
    assert resolve_benchmark("AAPL", {"market": "US"}) == "SPY"
    # International suffix map still works
    assert resolve_benchmark("7203.T", {"market": "US"}) == "^N225"


# ---------------------------------------------------------------------------
# 5. Elimination of Direct Yahoo Imports Outside router/vendors
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_no_direct_yahoo_imports_in_agents_or_memory():
    """Verify that neither tradingagents/agents/ nor tradingagents/memory/
    imports from tradingagents.dataflows.vendors.yahoo directly."""
    target_dirs = [
        ROOT / "tradingagents" / "agents",
        ROOT / "tradingagents" / "memory",
    ]

    offenders = []
    for directory in target_dirs:
        for py_file in directory.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if "vendors.yahoo" in node.module or node.module.endswith(".yahoo"):
                        offenders.append(f"{py_file.name}: from {node.module}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if "vendors.yahoo" in alias.name:
                            offenders.append(f"{py_file.name}: import {alias.name}")

    assert offenders == [], f"Direct Yahoo imports found: {offenders}"


# ---------------------------------------------------------------------------
# 6. Strict Yahoo Isolation: Zero Yahoo Calls for market="VN"
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_vietnam_never_invokes_yahoo(monkeypatch):
    """Ensure that with market="VN", no Yahoo Finance code is ever called across:
    - resolve_instrument_identity
    - get_verified_market_snapshot
    - get_closes
    - route_to_vendor (stock, indicators, fundamentals, news)
    """
    yahoo_mock = MagicMock(side_effect=AssertionError("Yahoo was invoked for market='VN'!"))

    # Patch yfinance Ticker and Yahoo vendor entry points to explode if called
    monkeypatch.setattr("tradingagents.dataflows.vendors.yahoo.market.yf.Ticker", yahoo_mock)
    monkeypatch.setattr(
        "tradingagents.dataflows.vendors.yahoo.fundamentals.get_company_profile", yahoo_mock
    )
    monkeypatch.setattr(
        "tradingagents.dataflows.vendors.yahoo.snapshot.build_verified_market_snapshot", yahoo_mock
    )
    monkeypatch.setattr("tradingagents.dataflows.vendors.yahoo.market.get_closes", yahoo_mock)
    monkeypatch.setattr("tradingagents.dataflows.vendors.yahoo.market.get_YFin_data_online", yahoo_mock)
    monkeypatch.setattr(
        "tradingagents.dataflows.vendors.yahoo.market.get_stock_stats_indicators_window", yahoo_mock
    )
    monkeypatch.setattr(
        "tradingagents.dataflows.vendors.yahoo.fundamentals.get_fundamentals", yahoo_mock
    )
    monkeypatch.setattr("tradingagents.dataflows.vendors.yahoo.news.get_news_yfinance", yahoo_mock)

    _identity.cache_clear()

    with run_config({"market": "VN"}):
        # 1. Identity lookup fails open without touching Yahoo
        identity = resolve_instrument_identity("VNM", market="VN")
        assert identity == {}

        # 2. Snapshot returns DATA_UNAVAILABLE without touching Yahoo
        snapshot_res = get_verified_market_snapshot.invoke(
            {"symbol": "VNM", "curr_date": "2026-05-10", "look_back_days": 30}
        )
        assert "DATA_UNAVAILABLE" in snapshot_res or "NO_DATA_AVAILABLE" in snapshot_res

        # 3. get_closes raises VendorUnavailableError without touching Yahoo
        with pytest.raises(Exception) as excinfo:
            get_closes("VNM", "2026-01-01", "2026-01-10")
        assert "Vietnam market vendor" in str(excinfo.value) or "DATA_UNAVAILABLE" in str(excinfo.value)

        # 4. Stock data routing
        stock_res = route_to_vendor("get_stock_data", "VNM", "2026-01-01", "2026-01-10")
        assert "DATA_UNAVAILABLE" in stock_res or "NO_DATA_AVAILABLE" in stock_res

        # 5. Technical indicators routing
        ind_res = route_to_vendor("get_indicators", "VNM", "close_50_sma", "2026-01-10")
        assert "DATA_UNAVAILABLE" in ind_res or "NO_DATA_AVAILABLE" in ind_res

        # 6. Fundamentals routing
        fund_res = route_to_vendor("get_fundamentals", "VNM", "2026-01-10")
        assert "DATA_UNAVAILABLE" in fund_res or "NO_DATA_AVAILABLE" in fund_res

        # 7. News routing
        news_res = route_to_vendor("get_news", "VNM", "2026-01-10")
        assert "DATA_UNAVAILABLE" in news_res or "NO_DATA_AVAILABLE" in news_res

    # Assert Yahoo mock was NEVER called once
    assert yahoo_mock.call_count == 0
