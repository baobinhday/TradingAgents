"""AlgoLab Fundamentals Adapter for company profile, valuation, and financial statements."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from tradingagents.dataflows.date_window import withhold_live_profile
from tradingagents.dataflows.errors import NoMarketDataError
from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.dataflows.vendors.algolab.client import AlgoLabClient
from tradingagents.dataflows.vendors.vn_lag import filter_algolab_statements_by_lag

logger = logging.getLogger(__name__)


def _statement_to_csv(lines_data: Any) -> str:
    """Format AlgoLab tabular lines into a clean CSV string."""
    if not lines_data:
        return ""
    if isinstance(lines_data, dict) and "columns" in lines_data and "rows" in lines_data:
        df = pd.DataFrame(lines_data["rows"], columns=lines_data["columns"])
        return df.to_csv(index=False)
    if isinstance(lines_data, list):
        df = pd.DataFrame(lines_data)
        return df.to_csv(index=False)
    return str(lines_data)


def get_company_profile(ticker: str) -> dict[str, Any]:
    """Retrieve raw profile dictionary from AlgoLab."""
    canonical = normalize_symbol(ticker)
    client = AlgoLabClient.get_instance()

    res = client.call_tool("get_company_profile", {"symbol": canonical})
    data = res.get("data", {}) if isinstance(res, dict) else {}
    if not data or not isinstance(data, dict):
        raise NoMarketDataError(symbol=ticker, canonical=canonical, detail="no profile data found")

    overview = data.get("overview", {}) or {}
    icb = overview.get("icb", {}) or {}
    valuation = data.get("valuation", {}) or {}
    val_algolab = valuation.get("algolabx", {}) or {}
    val_vendor = valuation.get("vendor", {}) or {}

    return {
        "symbol": canonical,
        "name": overview.get("name"),
        "company_name": overview.get("name"),
        "exchange": overview.get("exchange"),
        "sector": icb.get("l2") or icb.get("l1"),
        "industry": icb.get("l4") or icb.get("l3"),
        "market_cap": overview.get("market_cap_vnd") or val_algolab.get("market_cap_vnd") or val_vendor.get("market_cap_vnd"),
        "outstanding_shares": overview.get("outstanding_shares") or val_algolab.get("shares_outstanding"),
        "pe": val_algolab.get("pe") or val_vendor.get("pe"),
        "pb": val_algolab.get("pb") or val_vendor.get("pb"),
        "eps": val_algolab.get("eps_ttm"),
        "bvps": val_algolab.get("bvps"),
        "dividend_yield": val_vendor.get("div_yield_pct"),
    }


def get_fundamentals(ticker: str, as_of_date: str = None) -> str:
    """Retrieve formatted company fundamentals overview from AlgoLab."""
    canonical = normalize_symbol(ticker)
    withheld = withhold_live_profile(as_of_date, canonical)
    if withheld:
        return withheld

    profile = get_company_profile(canonical)

    fields = [
        ("Symbol", profile.get("symbol")),
        ("Name", profile.get("name")),
        ("Exchange", profile.get("exchange")),
        ("Sector", profile.get("sector")),
        ("Industry", profile.get("industry")),
        ("Market Cap (VND)", f"{profile.get('market_cap'):,}" if profile.get("market_cap") else None),
        ("Outstanding Shares", f"{profile.get('outstanding_shares'):,}" if profile.get("outstanding_shares") else None),
        ("P/E Ratio (TTM)", profile.get("pe")),
        ("P/B Ratio", profile.get("pb")),
        ("EPS TTM (VND)", f"{profile.get('eps'):,}" if profile.get("eps") else None),
        ("Book Value Per Share (VND)", f"{profile.get('bvps'):,}" if profile.get("bvps") else None),
        ("Dividend Yield (%)", profile.get("dividend_yield")),
    ]

    lines = [f"## Fundamentals for {canonical}:", ""]
    for label, val in fields:
        if val is not None:
            lines.append(f"- **{label}**: {val}")

    return "\n".join(lines)


def _get_financial_statement(
    ticker: str,
    statement_type: str,
    freq: str = "quarterly",
    as_of_date: str = None,
    title: str = "Financial Statement",
) -> str:
    canonical = normalize_symbol(ticker)
    client = AlgoLabClient.get_instance()
    period = "quarter" if freq.lower() in ("quarterly", "quarter") else "annual"

    res = client.call_tool(
        "get_financial_statements",
        {"symbol": canonical, "statement": statement_type, "period": period, "limit": 8},
    )

    data = res.get("data", {}) if isinstance(res, dict) else {}
    if not data or not isinstance(data, dict):
        raise NoMarketDataError(symbol=ticker, canonical=canonical, detail=f"no {statement_type} data found")

    lines_data = data.get("lines")
    if as_of_date and lines_data:
        lines_data, _ = filter_algolab_statements_by_lag(lines_data, as_of_date)

    csv_body = _statement_to_csv(lines_data)
    if not csv_body or (isinstance(lines_data, dict) and len(lines_data.get("columns", [])) <= 1):
        raise NoMarketDataError(symbol=ticker, canonical=canonical, detail=f"no {statement_type} data published as of {as_of_date}")

    header = f"# {title} data for {canonical} ({freq})\n"
    return header + csv_body


def get_balance_sheet(ticker: str, freq: str = "quarterly", as_of_date: str = None) -> str:
    """Retrieve balance sheet data from AlgoLab."""
    return _get_financial_statement(ticker, "balance", freq, as_of_date, "Balance Sheet")


def get_cashflow(ticker: str, freq: str = "quarterly", as_of_date: str = None) -> str:
    """Retrieve cash flow data from AlgoLab."""
    return _get_financial_statement(ticker, "cash", freq, as_of_date, "Cash Flow")


def get_income_statement(ticker: str, freq: str = "quarterly", as_of_date: str = None) -> str:
    """Retrieve income statement data from AlgoLab."""
    return _get_financial_statement(ticker, "income", freq, as_of_date, "Income Statement")
