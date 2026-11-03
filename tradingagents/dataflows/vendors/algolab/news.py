"""AlgoLab News and Corporate Events Adapter."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd
from dateutil.relativedelta import relativedelta

from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.dataflows.vendors.algolab.client import AlgoLabClient

logger = logging.getLogger(__name__)


def _normalize_items(items: Any) -> list[dict[str, Any]]:
    """Normalize news items into a list of dictionaries whether returned as list or columnar dict."""
    if isinstance(items, list):
        return items
    if isinstance(items, dict) and "columns" in items and "rows" in items:
        cols = items.get("columns", [])
        rows = items.get("rows", [])
        return [dict(zip(cols, row, strict=False)) for row in rows]
    return []


def _format_articles(articles: list[dict[str, Any]]) -> str:
    """Format news article items into structured markdown."""
    out = []
    for art in articles:
        content = art.get("content") or art.get("summary") or ""
        title = art.get("title")
        if not title and content:
            lines = [line.strip("#* \t") for line in str(content).splitlines() if line.strip()]
            title = lines[0] if lines else "Market Recap"
        title = title or "No title"

        source = art.get("source") or "AlgoLab"
        sentiment = art.get("sentiment")
        sentiment_str = f", sentiment: {sentiment}" if sentiment else ""
        pub_at = art.get("published_at") or art.get("date") or ""
        date_str = f" ({pub_at[:10]})" if pub_at else ""

        out.append(f"### {title} (source: {source}{sentiment_str}){date_str}")
        if content and content != title:
            out.append(content)
        url = art.get("url")
        if url:
            out.append(f"Link: {url}")
        out.append("")
    return "\n".join(out)


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    """Retrieve news for a company from AlgoLab."""
    canonical = normalize_symbol(ticker)
    client = AlgoLabClient.get_instance()

    res = client.call_tool(
        "get_news",
        {"symbol": canonical, "kind": "company", "from_date": start_date, "limit": 50},
    )

    data = res.get("data", {}) if isinstance(res, dict) else {}
    items = _normalize_items(data.get("items") if isinstance(data, dict) else [])

    # Filter articles within [start_date, end_date]
    in_window = []
    for art in items:
        pub = art.get("published_at") or ""
        pub_date = pub[:10] if len(pub) >= 10 else ""
        if not pub_date or (pub_date >= start_date and pub_date <= end_date):
            in_window.append(art)

    if not in_window:
        return f"No news found for {canonical} between {start_date} and {end_date}"

    body = _format_articles(in_window)
    return f"## News for {canonical} from {start_date} to {end_date}:\n\n{body}"


def get_global_news(as_of_date: str, look_back_days: int = 7, limit: int = 10) -> str:
    """Retrieve market recap and economy news from AlgoLab."""
    curr_dt = datetime.strptime(as_of_date, "%Y-%m-%d")
    start_dt = curr_dt - relativedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    client = AlgoLabClient.get_instance()
    res = client.call_tool(
        "get_news",
        {"kind": "recap", "from_date": start_date, "limit": limit},
    )

    data = res.get("data", {}) if isinstance(res, dict) else {}
    items = _normalize_items(data.get("items") if isinstance(data, dict) else [])

    if not items:
        # Fallback to expert news
        res = client.call_tool(
            "get_news",
            {"kind": "expert", "from_date": start_date, "limit": limit},
        )
        data = res.get("data", {}) if isinstance(res, dict) else {}
        items = _normalize_items(data.get("items") if isinstance(data, dict) else [])

    if not items:
        return f"No market recap news found between {start_date} and {as_of_date}"

    body = _format_articles(items[:limit])
    return f"## Vietnam Market Recap News, from {start_date} to {as_of_date}:\n\n{body}"


def get_insider_transactions(ticker: str, as_of_date: str = None) -> str:
    """Retrieve corporate events and insider transactions from AlgoLab."""
    canonical = normalize_symbol(ticker)
    client = AlgoLabClient.get_instance()

    res = client.call_tool(
        "call_function",
        {"name": "get_corporate_events", "arguments": {"symbol": canonical}},
    )

    data = res.get("data", {}) if isinstance(res, dict) else {}
    events = data.get("events") if isinstance(data, dict) else None

    if not events:
        return f"No corporate events or insider transactions reported for symbol '{canonical}'"

    if isinstance(events, dict) and "columns" in events and "rows" in events:
        df = pd.DataFrame(events["rows"], columns=events["columns"])
    elif isinstance(events, list):
        df = pd.DataFrame(events)
    else:
        return f"No corporate events or insider transactions reported for symbol '{canonical}'"

    if df.empty:
        return f"No corporate events or insider transactions reported for symbol '{canonical}'"

    return f"# Corporate Events & Insider Transactions for {canonical}\n" + df.to_csv(index=False)
