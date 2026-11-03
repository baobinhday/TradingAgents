"""SSI Market Data Adapter for daily OHLCV and close prices."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd

from tradingagents.dataflows.errors import NoMarketDataError
from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.dataflows.vendors.ssi.client import SSIMCPClient

logger = logging.getLogger(__name__)

INDEX_SYMBOLS = {"VNINDEX", "VN30", "HNX30", "HNXINDEX", "UPCOMINDEX"}


def _parse_ssi_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Parse SSI stock or index records into standard OHLCV DataFrame."""
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Map trading_date (DD/MM/YYYY) to Date (YYYY-MM-DD)
    if "trading_date" in df.columns:
        df["Date"] = pd.to_datetime(df["trading_date"], format="%d/%m/%Y", errors="coerce").dt.strftime("%Y-%m-%d")
    elif "date" in df.columns:
        df["Date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    else:
        return pd.DataFrame()

    rename_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }
    df = df.rename(columns=rename_map)

    required = ["Date", "Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            return pd.DataFrame()

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop zero volume bars
    df = df[df["Volume"].notna() & (df["Volume"] > 0)]
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    return df[required]


def _fetch_ssi_ohlcv(symbol: str, end_date: str | None = None) -> pd.DataFrame:
    """Fetch raw OHLCV records from SSI MCP."""
    canonical = normalize_symbol(symbol)
    client = SSIMCPClient.get_instance()

    # Format toDate as DD/MM/YYYY if provided
    to_date_str = None
    if end_date:
        try:
            dt = datetime.strptime(end_date[:10], "%Y-%m-%d")
            to_date_str = dt.strftime("%d/%m/%Y")
        except Exception:
            to_date_str = None

    if canonical.upper() in INDEX_SYMBOLS:
        args = {"indexCode": canonical.upper(), "range": "max_range"}
        if to_date_str:
            args["to"] = to_date_str
        res = client.call_tool("marketdata_list_index_daily_data", args)
        data = res.get("data", {}) if isinstance(res, dict) else {}
        records = data.get("indices", []) if isinstance(data, dict) else []
    else:
        args = {"symbol": canonical.upper(), "range": "max_range"}
        if to_date_str:
            args["toDate"] = to_date_str
        res = client.call_tool("marketdata_list_stock_daily_data", args)
        data = res.get("data", {}) if isinstance(res, dict) else {}
        records = data.get("stocks", []) if isinstance(data, dict) else []

    return _parse_ssi_records(records)


def get_stock_data(symbol: str, start_date: str, end_date: str) -> str:
    """Retrieve daily OHLCV CSV data for a symbol from SSI MCP."""
    canonical = normalize_symbol(symbol)
    df = _fetch_ssi_ohlcv(canonical, end_date)

    if df.empty:
        raise NoMarketDataError(
            symbol=symbol,
            canonical=canonical,
            detail=f"no price rows between {start_date} and {end_date}",
        )

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
    df = _fetch_ssi_ohlcv(canonical, end_date)

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
    df = _fetch_ssi_ohlcv(canonical, as_of_date)

    if df.empty:
        raise NoMarketDataError(symbol, canonical, f"no price rows on or before {as_of_date}")

    df = df[df["Date"] <= as_of_date].sort_values("Date").reset_index(drop=True)
    if df.empty:
        raise NoMarketDataError(symbol, canonical, f"no price rows on or before {as_of_date}")

    return df
