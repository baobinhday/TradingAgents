"""SSI News and Corporate Actions Adapter."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd
from dateutil.relativedelta import relativedelta

from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.dataflows.vendors.ssi.client import SSIMCPClient

logger = logging.getLogger(__name__)


def _format_ssi_articles(articles: list[dict[str, Any]]) -> str:
    """Format SSI news items into structured markdown."""
    out = []
    for art in articles:
        title = art.get("title") or "No title"
        source = art.get("news_source") or "SSI"
        pub = art.get("public_date") or art.get("update_date") or ""
        date_str = f" ({pub[:10]})" if pub else ""

        out.append(f"### {title} (source: {source}){date_str}")
        summary = art.get("short_content") or art.get("summary")
        if summary:
            out.append(summary)
        link = art.get("news_source_link") or art.get("url")
        if link:
            out.append(f"Link: {link}")
        out.append("")
    return "\n".join(out)


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    """Retrieve news about a company from SSI MCP."""
    canonical = normalize_symbol(ticker)
    client = SSIMCPClient.get_instance()

    to_str = None
    try:
        dt = datetime.strptime(end_date[:10], "%Y-%m-%d")
        to_str = dt.strftime("%d/%m/%Y")
    except Exception:
        to_str = None

    args: dict[str, Any] = {"symbol": canonical.upper(), "range": "6m", "pageSize": 50}
    if to_str:
        args["to"] = to_str

    res = client.call_tool("marketdata_list_company_news", args)
    data = res.get("data", {}) if isinstance(res, dict) else {}
    items = data.get("news", []) if isinstance(data, dict) else []

    if not items:
        return f"No news found for {canonical} between {start_date} and {end_date}"

    body = _format_ssi_articles(items)
    return f"## News for {canonical} from {start_date} to {end_date}:\n\n{body}"


def get_global_news(as_of_date: str, look_back_days: int = 7, limit: int = 10) -> str:
    """Retrieve market news from SSI MCP."""
    client = SSIMCPClient.get_instance()

    to_str = None
    try:
        dt = datetime.strptime(as_of_date[:10], "%Y-%m-%d")
        to_str = dt.strftime("%d/%m/%Y")
    except Exception:
        to_str = None

    args: dict[str, Any] = {"range": "1m", "pageSize": limit}
    if to_str:
        args["to"] = to_str

    res = client.call_tool("marketdata_list_company_news", args)
    data = res.get("data", {}) if isinstance(res, dict) else {}
    items = data.get("news", []) if isinstance(data, dict) else []

    if not items:
        return f"No market news found for as_of_date {as_of_date}"

    curr_dt = datetime.strptime(as_of_date, "%Y-%m-%d")
    start_dt = curr_dt - relativedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    body = _format_ssi_articles(items[:limit])
    return f"## Vietnam Market News, from {start_date} to {as_of_date}:\n\n{body}"


def get_insider_transactions(ticker: str, as_of_date: str = None) -> str:
    """Retrieve corporate actions and insider transactions from SSI MCP."""
    canonical = normalize_symbol(ticker)
    client = SSIMCPClient.get_instance()

    res = client.call_tool(
        "marketdata_list_corporate_actions",
        {"symbol": canonical.upper(), "range": "1y", "pageSize": 50},
    )
    data = res.get("data", {}) if isinstance(res, dict) else {}
    items = data.get("corporate_actions", []) if isinstance(data, dict) else []

    if not items:
        return f"No corporate actions or insider transactions reported for symbol '{canonical}'"

    df = pd.DataFrame(items)
    return f"# Corporate Actions & Insider Transactions for {canonical}\n" + df.to_csv(index=False)
