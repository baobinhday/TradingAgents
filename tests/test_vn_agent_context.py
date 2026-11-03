"""Unit tests for Vietnam equity agent context, market rules, reporting lag, and social analyst placeholder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
from tradingagents.agents.analysts.news_analyst import create_news_analyst
from tradingagents.agents.analysts.sentiment_analyst import (
    SENTIMENT_DATA_UNAVAILABLE,
    create_sentiment_analyst,
)
from tradingagents.agents.context import (
    build_instrument_context,
    get_instrument_context_from_state,
)
from tradingagents.agents.schemas import SentimentBand, SentimentReport, render_sentiment_report
from tradingagents.dataflows.config import run_config
from tradingagents.dataflows.router import route_to_vendor
from tradingagents.dataflows.vendors.vn_lag import (
    filter_algolab_statements_by_lag,
    filter_ssi_statements_by_lag,
    get_vn_period_publication_date,
    is_period_published,
)

# ==============================================================================
# 1. Market Knowledge & Trading Rules in Context
# ==============================================================================

@pytest.mark.unit
def test_build_instrument_context_vietnam_rules():
    """Verify Vietnam equity rules are injected when market='VN'."""
    ctx = build_instrument_context("VNM", asset_type="stock", market="VN")
    assert "The instrument to analyze is `VNM`" in ctx
    assert "Vietnam Equity Market Rules" in ctx
    assert "HOSE (±7% daily price limit)" in ctx
    assert "HNX (±10%)" in ctx
    assert "UPCoM (±15%)" in ctx
    assert "Trading hours 9:00-15:00 UTC+7" in ctx
    assert "Settlement cycle is T+2.5" in ctx
    assert "VND" in ctx
    assert "Foreign ownership limits (FOL/room)" in ctx
    assert "[Source: AlgoLab]" in ctx
    assert "[Source: SSI]" in ctx


@pytest.mark.unit
def test_build_instrument_context_vietnam_suffix():
    """Verify ticker with .VN suffix auto-triggers Vietnam equity rules."""
    ctx = build_instrument_context("FPT.VN", asset_type="stock")
    assert "Vietnam Equity Market Rules" in ctx
    assert "T+2.5" in ctx


@pytest.mark.unit
def test_build_instrument_context_us_equity_no_vietnam_rules():
    """Verify US stock does not have Vietnam market rules."""
    ctx = build_instrument_context("AAPL", asset_type="stock", market="US")
    assert "Vietnam Equity Market Rules" not in ctx
    assert "T+2.5" not in ctx


@pytest.mark.unit
def test_get_instrument_context_from_state_vietnam():
    state = {
        "company_of_interest": "HPG",
        "trade_date": "2026-10-15",
        "market": "VN",
    }
    ctx = get_instrument_context_from_state(state)
    assert "Vietnam Equity Market Rules" in ctx
    assert "HPG" in ctx


# ==============================================================================
# 2. Point-in-Time Financial Statements & Simulated Reporting Lag
# ==============================================================================

@pytest.mark.unit
def test_vn_period_publication_date_quarterly():
    """Test 45-day statutory lag for quarterly statements."""
    # Q1: 03-31 + 45 days -> 05-15
    assert get_vn_period_publication_date("2026-Q1") == "2026-05-15"
    assert get_vn_period_publication_date("2026Q1") == "2026-05-15"
    assert get_vn_period_publication_date("Q1/2026") == "2026-05-15"

    # Q2: 06-30 + 45 days -> 08-14
    assert get_vn_period_publication_date("2026-Q2") == "2026-08-14"

    # Q3: 09-30 + 45 days -> 11-14
    assert get_vn_period_publication_date("2026-Q3") == "2026-11-14"

    # Q4: 12-31 + 45 days -> 02-14 of next year
    assert get_vn_period_publication_date("2025-Q4") == "2026-02-14"


@pytest.mark.unit
def test_vn_period_publication_date_annual():
    """Test 90-day statutory lag for annual statements."""
    # 2025 FY ends 2025-12-31 + 90 days -> 2026-03-31
    assert get_vn_period_publication_date("2025") == "2026-03-31"
    assert get_vn_period_publication_date("FY2025") == "2026-03-31"


@pytest.mark.unit
def test_vn_period_publication_date_dict_repr():
    """Test SSI dictionary format with year_report and length_report."""
    # Q3 2026 (length_report = 3)
    assert get_vn_period_publication_date({"year_report": 2026, "length_report": 3}) == "2026-11-14"
    # FY 2025 (length_report = 5)
    assert get_vn_period_publication_date({"year_report": 2025, "length_report": 5}) == "2026-03-31"


@pytest.mark.unit
def test_vn_period_publication_date_non_period_returns_none():
    assert get_vn_period_publication_date("revenue") is None
    assert get_vn_period_publication_date("item") is None
    assert get_vn_period_publication_date("Chỉ tiêu") is None
    assert get_vn_period_publication_date(None) is None


@pytest.mark.unit
def test_is_period_published():
    # 2026-Q3 published on 2026-11-14
    assert not is_period_published("2026-Q3", "2026-10-15")
    assert is_period_published("2026-Q3", "2026-11-14")
    assert is_period_published("2026-Q3", "2026-11-20")

    # Non-period indicators are always considered published (preserved)
    assert is_period_published("item", "2026-10-15")


@pytest.mark.unit
def test_filter_algolab_statements_by_lag():
    """Verify that columns for unpublished periods are dropped."""
    lines_data = {
        "columns": ["item", "2026-Q3", "2026-Q2", "2026-Q1"],
        "rows": [
            ["Revenue", 1000, 950, 900],
            ["Net Profit", 150, 140, 130],
        ],
    }

    # As of 2026-10-15: 2026-Q3 is published 2026-11-14 (> as_of_date), so it must be dropped.
    filtered, dropped = filter_algolab_statements_by_lag(lines_data, "2026-10-15")
    assert dropped == 1
    assert filtered["columns"] == ["item", "2026-Q2", "2026-Q1"]
    assert filtered["rows"] == [
        ["Revenue", 950, 900],
        ["Net Profit", 140, 130],
    ]

    # As of 2026-11-15: 2026-Q3 is published, so all columns are preserved.
    filtered_all, dropped_all = filter_algolab_statements_by_lag(lines_data, "2026-11-15")
    assert dropped_all == 0
    assert len(filtered_all["columns"]) == 4


@pytest.mark.unit
def test_filter_ssi_statements_by_lag():
    items = [
        {"year_report": 2026, "length_report": 3, "revenue": 1000},  # pub 2026-11-14
        {"year_report": 2026, "length_report": 2, "revenue": 950},   # pub 2026-08-14
        {"year_report": 2025, "length_report": 5, "revenue": 3800},  # pub 2026-03-31
    ]

    # As of 2026-10-15: 2026-Q3 must be dropped
    filtered = filter_ssi_statements_by_lag(items, "2026-10-15")
    assert len(filtered) == 2
    assert filtered[0]["length_report"] == 2
    assert filtered[1]["length_report"] == 5

    # As of 2026-02-15: 2026-Q3, 2026-Q2, and 2025-FY (pub 2026-03-31) must all be dropped
    filtered_early = filter_ssi_statements_by_lag(items, "2026-02-15")
    assert len(filtered_early) == 0


# ==============================================================================
# 3. Social Analyst Placeholder Tests
# ==============================================================================

@pytest.mark.unit
def test_sentiment_analyst_vietnam_placeholder_skips_network_and_llm():
    """Verify that for market='VN', sentiment analyst returns placeholder with zero LLM/network calls."""
    mock_llm = MagicMock()

    analyst_node = create_sentiment_analyst(mock_llm)

    state = {
        "company_of_interest": "VNM",
        "trade_date": "2026-10-15",
        "market": "VN",
        "messages": [],
    }

    with (
        patch("tradingagents.agents.tools.get_news.func") as mock_news,
        patch("tradingagents.agents.analysts.sentiment_analyst.fetch_stocktwits_messages") as mock_st,
        patch("tradingagents.agents.analysts.sentiment_analyst.fetch_reddit_posts") as mock_reddit,
    ):
        result = analyst_node(state)

    # 1. Zero network calls
    mock_news.assert_not_called()
    mock_st.assert_not_called()
    mock_reddit.assert_not_called()

    # 2. Zero LLM calls
    mock_llm.invoke.assert_not_called()

    # 3. Returns standardized placeholder report
    assert "sentiment_report" in result
    report_text = result["sentiment_report"]
    assert "**Overall Sentiment:** **Unavailable**" in report_text
    assert "**Confidence:** Low" in report_text
    assert "Vietnam Social Sentiment: UNAVAILABLE" in report_text
    assert "NOT a neutral signal" in report_text
    assert report_text == SENTIMENT_DATA_UNAVAILABLE


@pytest.mark.unit
def test_sentiment_report_schema_supports_unavailable():
    """Verify SentimentReport schema with UNAVAILABLE band and optional overall_score."""
    report = SentimentReport(
        overall_band=SentimentBand.UNAVAILABLE,
        overall_score=None,
        confidence="low",
        narrative="Social chatter unavailable.",
    )
    rendered = render_sentiment_report(report)
    assert "**Overall Sentiment:** **Unavailable**" in rendered
    assert "(Score:" not in rendered
    assert "**Confidence:** Low" in rendered
    assert "Social chatter unavailable." in rendered


# ==============================================================================
# 4. Source-Aware Multi-Source Co-Sourcing & Prompts
# ==============================================================================

@pytest.mark.unit
def test_co_sourcing_conflicting_figures_displays_both_sources(monkeypatch):
    """Test fixture where AlgoLab and SSI report conflicting metrics:
    Both sources must appear with their labeled headers in the final output.
    """
    algolab_fund = "## Fundamentals for VNM:\n- **P/E Ratio (TTM)**: 15.2\n- **ROE**: 24.5%"
    ssi_fund = "## Fundamentals for VNM:\n- **P/E Ratio**: 17.8\n- **ROE**: 28.1%"

    from tradingagents.dataflows.router import VENDOR_METHODS

    monkeypatch.setitem(VENDOR_METHODS["get_fundamentals"], "algolab", lambda ticker, as_of_date=None: algolab_fund)
    monkeypatch.setitem(VENDOR_METHODS["get_fundamentals"], "ssi", lambda ticker, as_of_date=None: ssi_fund)

    with run_config({"market": "VN"}):
        result = route_to_vendor("get_fundamentals", "VNM")

    assert "### [Source: AlgoLab]" in result
    assert "P/E Ratio (TTM)**: 15.2" in result
    assert "### [Source: SSI]" in result
    assert "P/E Ratio**: 17.8" in result


@pytest.mark.unit
def test_news_analyst_prompt_contains_source_and_window_guidance():
    mock_llm = MagicMock()
    with patch("tradingagents.agents.analysts.news_analyst.take_turn") as mock_turn:
        mock_turn.return_value = (MagicMock(), "news report text")
        node = create_news_analyst(mock_llm)
        state = {
            "company_of_interest": "VNM",
            "trade_date": "2026-10-15",
            "market": "VN",
            "messages": [],
        }
        res = node(state)
        assert res["news_report"] == "news report text"
        # Prompt passed to take_turn
        prompt_passed = mock_turn.call_args[0][0]
        rendered = prompt_passed.format(messages=[])
        assert "vendor coverage windows" in rendered
        assert "[Source: AlgoLab] or [Source: SSI]" in rendered


@pytest.mark.unit
def test_fundamentals_analyst_prompt_contains_lag_and_cosource_guidance():
    mock_llm = MagicMock()
    with patch("tradingagents.agents.analysts.fundamentals_analyst.take_turn") as mock_turn:
        mock_turn.return_value = (MagicMock(), "fundamentals report text")
        node = create_fundamentals_analyst(mock_llm)
        state = {
            "company_of_interest": "VNM",
            "trade_date": "2026-10-15",
            "market": "VN",
            "messages": [],
        }
        res = node(state)
        assert res["fundamentals_report"] == "fundamentals report text"
        prompt_passed = mock_turn.call_args[0][0]
        rendered = prompt_passed.format(messages=[])
        assert "statutory reporting lag" in rendered
        assert "[Source: AlgoLab] and [Source: SSI]" in rendered
