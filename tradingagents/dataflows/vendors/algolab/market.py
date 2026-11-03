"""AlgoLab Market Data Adapter for daily OHLCV and close prices."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd
from dateutil.relativedelta import relativedelta

from tradingagents.dataflows.errors import NoMarketDataError
from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.dataflows.vendors.algolab.client import AlgoLabClient

logger = logging.getLogger(__name__)


def _parse_bars(bars_data: Any) -> pd.DataFrame:
    """Parse AlgoLab bars structure into a pandas DataFrame."""
    if not bars_data:
        return pd.DataFrame()

    if isinstance(bars_data, dict) and "columns" in bars_data and "rows" in bars_data:
        df = pd.DataFrame(bars_data["rows"], columns=bars_data["columns"])
    elif isinstance(bars_data, list):
        df = pd.DataFrame(bars_data)
    else:
        return pd.DataFrame()

    # Map column names to standard OHLCV
    rename_map = {
        "t": "Date",
        "o": "Open",
        "h": "High",
        "l": "Low",
        "c": "Close",
        "v": "Volume",
    }
    df = df.rename(columns=rename_map)

    required = ["Date", "Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            return pd.DataFrame()

    # Normalize Date to YYYY-MM-DD
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["Date"])

    # Ensure numeric types
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop zero-volume unfinished or empty session bars
    df = df[df["Volume"].notna() & (df["Volume"] > 0)]

    df = df.sort_values("Date").reset_index(drop=True)
    return df[required]


def get_stock_data(symbol: str, start_date: str, end_date: str) -> str:
    """Retrieve daily OHLCV CSV data for a Vietnam symbol from AlgoLab."""
    canonical = normalize_symbol(symbol)
    client = AlgoLabClient.get_instance()

    res = client.call_tool(
        "get_price_history",
        {
            "symbol": canonical,
            "interval": "1d",
            "from_date": start_date,
            "to_date": end_date,
            "limit": 1000,
        },
    )

    data = res.get("data", {}) if isinstance(res, dict) else {}
    bars = data.get("bars") if isinstance(data, dict) else None
    df = _parse_bars(bars)

    if df.empty:
        raise NoMarketDataError(
            symbol=symbol,
            canonical=canonical,
            detail=f"no price rows between {start_date} and {end_date}",
        )

    # Filter to requested inclusive window [start_date, end_date]
    df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].reset_index(drop=True)
    if df.empty:
        raise NoMarketDataError(
            symbol=symbol,
            canonical=canonical,
            detail=f"no price rows between {start_date} and {end_date}",
        )

    label = canonical if canonical == symbol.upper() else f"{canonical} (from {symbol})"
    header = f"# Stock data for {label} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(df)}\n\n"

    return header + df.to_csv(index=False)


def get_closes(symbol: str, start_date: str, end_date: str) -> pd.Series:
    """Retrieve daily close prices from start_date up to, not including, end_date."""
    canonical = normalize_symbol(symbol)
    client = AlgoLabClient.get_instance()

    res = client.call_tool(
        "get_price_history",
        {
            "symbol": canonical,
            "interval": "1d",
            "from_date": start_date,
            "to_date": end_date,
            "limit": 1000,
        },
    )

    data = res.get("data", {}) if isinstance(res, dict) else {}
    bars = data.get("bars") if isinstance(data, dict) else None
    df = _parse_bars(bars)

    if df.empty:
        return pd.Series(dtype=float)

    # Exclusive end_date
    df = df[(df["Date"] >= start_date) & (df["Date"] < end_date)]
    if df.empty:
        return pd.Series(dtype=float)

    df["dt"] = pd.to_datetime(df["Date"])
    return pd.Series(df["Close"].values, index=df["dt"], dtype=float)


def get_ohlcv_dataframe(symbol: str, as_of_date: str, look_back_days: int = 300) -> pd.DataFrame:
    """Retrieve OHLCV DataFrame on or before as_of_date for indicators and snapshots."""
    canonical = normalize_symbol(symbol)
    as_of_dt = datetime.strptime(as_of_date, "%Y-%m-%d")
    start_dt = as_of_dt - relativedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    client = AlgoLabClient.get_instance()
    res = client.call_tool(
        "get_price_history",
        {
            "symbol": canonical,
            "interval": "1d",
            "from_date": start_date,
            "to_date": as_of_date,
            "limit": 1000,
        },
    )

    data = res.get("data", {}) if isinstance(res, dict) else {}
    bars = data.get("bars") if isinstance(data, dict) else None
    df = _parse_bars(bars)

    if df.empty:
        raise NoMarketDataError(symbol, canonical, f"no price rows on or before {as_of_date}")

    df = df[df["Date"] <= as_of_date].sort_values("Date").reset_index(drop=True)
    if df.empty:
        raise NoMarketDataError(symbol, canonical, f"no price rows on or before {as_of_date}")

    return df
