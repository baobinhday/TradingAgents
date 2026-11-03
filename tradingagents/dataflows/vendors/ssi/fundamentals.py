"""SSI Fundamentals Adapter for company profile, financial ratios, and statements."""

from __future__ import annotations

import contextlib
import logging
from typing import Any

import pandas as pd

from tradingagents.dataflows.date_window import withhold_live_profile
from tradingagents.dataflows.errors import NoMarketDataError
from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.dataflows.vendors.ssi.client import SSIMCPClient
from tradingagents.dataflows.vendors.vn_lag import filter_ssi_statements_by_lag

logger = logging.getLogger(__name__)


def get_company_profile(ticker: str) -> dict[str, Any]:
    """Retrieve raw profile dictionary from SSI MCP."""
    canonical = normalize_symbol(ticker)
    client = SSIMCPClient.get_instance()

    res = client.call_tool("marketdata_list_company_profile", {"symbol": canonical.upper()})
    data = res.get("data", {}) if isinstance(res, dict) else {}
    profiles = data.get("company_profiles", []) if isinstance(data, dict) else []
    if not profiles and isinstance(data, dict) and "company_profile" in data:
        profiles = [data["company_profile"]]

    if not profiles:
        raise NoMarketDataError(symbol=ticker, canonical=canonical, detail="no SSI profile data found")

    p = profiles[0]
    return {
        "symbol": canonical,
        "name": p.get("company_name") or p.get("organ_name"),
        "company_name": p.get("company_name") or p.get("organ_name"),
        "exchange": p.get("com_group_code") or p.get("exchange"),
        "sector": p.get("icb_name") or p.get("industry_name"),
        "industry": p.get("icb_name"),
        "summary": p.get("overview") or p.get("business_summary"),
    }


def get_fundamentals(ticker: str, as_of_date: str = None) -> str:
    """Retrieve formatted company fundamentals overview from SSI MCP."""
    canonical = normalize_symbol(ticker)
    withheld = withhold_live_profile(as_of_date, canonical)
    if withheld:
        return withheld

    client = SSIMCPClient.get_instance()

    # 1. Profile
    profile = {}
    with contextlib.suppress(Exception):
        profile = get_company_profile(canonical)

    # 2. Financial ratios
    res = client.call_tool(
        "fundamental_list_financial_ratios",
        {"symbol": canonical.upper(), "pageSize": 10, "orderBy": "YearReport", "order": "DESC"},
    )
    data = res.get("data", {}) if isinstance(res, dict) else {}
    indicators = data.get("indicators", []) if isinstance(data, dict) else []

    latest_ind = indicators[0] if indicators else {}

    fields = [
        ("Symbol", canonical),
        ("Name", profile.get("name")),
        ("Exchange", profile.get("exchange")),
        ("Sector", profile.get("sector")),
        ("P/E Ratio", latest_ind.get("pe")),
        ("P/B Ratio", latest_ind.get("pb")),
        ("EPS (VND)", latest_ind.get("eps")),
        ("Book Value (VND)", latest_ind.get("book_value")),
        ("ROE", f"{float(latest_ind['roe']) * 100:.2f}%" if latest_ind.get("roe") else None),
        ("ROA", f"{float(latest_ind['roa']) * 100:.2f}%" if latest_ind.get("roa") else None),
        ("Debt/Equity", latest_ind.get("debt_to_equity")),
        ("Dividend Yield", f"{float(latest_ind['dividend_yield']) * 100:.2f}%" if latest_ind.get("dividend_yield") else None),
        ("Market Cap", latest_ind.get("market_cap")),
    ]

    lines = [f"## Fundamentals for {canonical}:", ""]
    for label, val in fields:
        if val is not None:
            lines.append(f"- **{label}**: {val}")

    return "\n".join(lines)


def _get_ssi_statement(
    ticker: str,
    tool_name: str,
    list_key: str,
    title: str,
    freq: str = "quarterly",
    as_of_date: str = None,
) -> str:
    canonical = normalize_symbol(ticker)
    client = SSIMCPClient.get_instance()

    res = client.call_tool(tool_name, {"symbol": canonical.upper(), "range": "1y", "pageSize": 10})
    data = res.get("data", {}) if isinstance(res, dict) else {}
    items = data.get(list_key, []) if isinstance(data, dict) else []

    if as_of_date and items:
        items = filter_ssi_statements_by_lag(items, as_of_date)

    if not items:
        raise NoMarketDataError(symbol=ticker, canonical=canonical, detail=f"no {title} data found on SSI")

    df = pd.DataFrame(items)
    # Drop columns that are completely null
    df = df.dropna(axis=1, how="all")
    header = f"# {title} data for {canonical} ({freq})\n"
    return header + df.to_csv(index=False)


def get_balance_sheet(ticker: str, freq: str = "quarterly", as_of_date: str = None) -> str:
    """Retrieve balance sheet from SSI MCP."""
    return _get_ssi_statement(
        ticker,
        "marketdata_list_finance_balance_sheet",
        "balance_sheets",
        "Balance Sheet",
        freq,
        as_of_date,
    )


def get_cashflow(ticker: str, freq: str = "quarterly", as_of_date: str = None) -> str:
    """Retrieve cash flow from SSI MCP."""
    return _get_ssi_statement(
        ticker,
        "marketdata_list_finance_cash_flow",
        "cash_flows",
        "Cash Flow",
        freq,
        as_of_date,
    )


def get_income_statement(ticker: str, freq: str = "quarterly", as_of_date: str = None) -> str:
    """Retrieve income statement from SSI MCP."""
    return _get_ssi_statement(
        ticker,
        "marketdata_list_finance_income_statement",
        "income_statements",
        "Income Statement",
        freq,
        as_of_date,
    )
