"""Technical indicators and verified snapshot calculation for Vietnam market symbols."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Annotated, Any

import pandas as pd
from dateutil.relativedelta import relativedelta
from stockstats import wrap

from tradingagents.dataflows.errors import NoMarketDataError, VendorUnavailableError
from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.dataflows.vendors.algolab.market import get_ohlcv_dataframe as get_algolab_ohlcv
from tradingagents.dataflows.vendors.ssi.market import get_ohlcv_dataframe as get_ssi_ohlcv
from tradingagents.dataflows.vendors.yahoo.common import price_text

logger = logging.getLogger(__name__)

DEFAULT_SNAPSHOT_INDICATORS: tuple[str, ...] = (
    "close_10_ema", "close_50_sma", "close_200_sma",
    "rsi", "boll", "boll_ub", "boll_lb",
    "macd", "macds", "macdh", "atr",
)

INDICATOR_DESCRIPTIONS: dict[str, str] = {
    "close_50_sma": (
        "50 SMA: A medium-term trend indicator. "
        "Usage: Identify trend direction and serve as dynamic support/resistance. "
        "Tips: It lags price; combine with faster indicators for timely signals."
    ),
    "close_200_sma": (
        "200 SMA: A long-term trend benchmark. "
        "Usage: Confirm overall market trend and identify golden/death cross setups. "
        "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
    ),
    "close_10_ema": (
        "10 EMA: A responsive short-term average. "
        "Usage: Capture quick shifts in momentum and potential entry points. "
        "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
    ),
    "macd": (
        "MACD: Computes momentum via differences of EMAs. "
        "Usage: Look for crossovers and divergence as signals of trend changes. "
        "Tips: Confirm with other indicators in low-volatility or sideways markets."
    ),
    "macds": (
        "MACD Signal: An EMA smoothing of the MACD line. "
        "Usage: Use crossovers with the MACD line to trigger trades. "
        "Tips: Should be part of a broader strategy to avoid false positives."
    ),
    "macdh": (
        "MACD Histogram: Shows the gap between the MACD line and its signal. "
        "Usage: Visualize momentum strength and spot divergence early. "
        "Tips: Can be volatile; complement with additional filters in fast-moving markets."
    ),
    "rsi": (
        "RSI: Measures momentum to flag overbought/oversold conditions. "
        "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
        "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
    ),
    "boll": (
        "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
        "Usage: Acts as a dynamic benchmark for price movement. "
        "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
    ),
    "boll_ub": (
        "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
        "Usage: Signals potential overbought conditions and breakout zones. "
        "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
    ),
    "boll_lb": (
        "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
        "Usage: Indicates potential oversold conditions. "
        "Tips: Use additional analysis to avoid false reversal signals."
    ),
    "atr": (
        "ATR: Averages true range to measure volatility. "
        "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
        "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
    ),
    "vwma": (
        "VWMA: A moving average weighted by volume. "
        "Usage: Confirm trends by integrating price action with volume data. "
        "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
    ),
    "mfi": (
        "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
        "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
        "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
    ),
}


def _fmt(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float):
        return price_text(value)
    return str(value)


def calculate_indicators_window(
    df: pd.DataFrame,
    symbol: str,
    indicator: str,
    as_of_date: str,
    look_back_days: int | None = 30,
) -> str:
    """Calculate technical indicator series over lookback window from OHLCV DataFrame."""
    if indicator not in INDICATOR_DESCRIPTIONS:
        raise ValueError(
            f"Indicator {indicator} is not supported. Please choose from: {list(INDICATOR_DESCRIPTIONS.keys())}"
        )

    normalize_symbol(symbol)
    look_back_days = look_back_days or 30
    as_of_dt = datetime.strptime(as_of_date, "%Y-%m-%d")
    before = as_of_dt - relativedelta(days=look_back_days)

    stock_df = wrap(df.copy())
    stock_df["Date"] = pd.to_datetime(stock_df["Date"]).dt.strftime("%Y-%m-%d")

    # Trigger calculation
    stock_df[indicator]

    indicator_map: dict[str, Any] = {}
    for _, row in stock_df.iterrows():
        d_str = row["Date"]
        val = row[indicator]
        indicator_map[d_str] = "N/A" if pd.isna(val) else val

    current_dt = as_of_dt
    date_values = []
    while current_dt >= before:
        date_str = current_dt.strftime("%Y-%m-%d")
        val = indicator_map.get(date_str, "N/A: Not a trading day (weekend or holiday)")
        date_values.append((date_str, val))
        current_dt = current_dt - relativedelta(days=1)

    ind_string = ""
    for date_str, value in date_values:
        ind_string += f"{date_str}: {value}\n"

    desc = INDICATOR_DESCRIPTIONS.get(indicator, "No description available.")
    return (
        f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {as_of_date}:\n\n"
        + ind_string
        + "\n\n"
        + desc
    )


def get_algolab_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    as_of_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "number of days of indicator values to fetch"] = 30,
) -> str:
    """Compute indicators for VN symbol using AlgoLab OHLCV data."""
    df = get_algolab_ohlcv(symbol, as_of_date, look_back_days=300)
    return calculate_indicators_window(df, symbol, indicator, as_of_date, look_back_days)


def get_ssi_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    as_of_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "number of days of indicator values to fetch"] = 30,
) -> str:
    """Compute indicators for VN symbol using SSI OHLCV data."""
    df = get_ssi_ohlcv(symbol, as_of_date, look_back_days=300)
    return calculate_indicators_window(df, symbol, indicator, as_of_date, look_back_days)


def render_vn_market_snapshot(
    df: pd.DataFrame,
    symbol: str,
    as_of_date: str,
    look_back_days: int = 30,
    indicators: Iterable[str] | None = None,
) -> str:
    """Render verified market snapshot markdown from OHLCV DataFrame."""
    canonical = normalize_symbol(symbol)
    stock_df = wrap(df.copy())
    selected = tuple(indicators or DEFAULT_SNAPSHOT_INDICATORS)

    indicator_values: dict[str, str] = {}
    for name in selected:
        try:
            stock_df[name]
            indicator_values[name] = _fmt(stock_df.iloc[-1][name])
        except Exception as exc:
            indicator_values[name] = f"N/A ({type(exc).__name__})"

    latest = df.iloc[-1]
    latest_date = _fmt(latest["Date"])
    window = max(1, min(int(look_back_days), 30))
    recent = df.tail(window)

    lines = [
        f"## Verified market data snapshot for {canonical}",
        "",
        f"- Requested analysis date: {as_of_date}",
        f"- Latest trading row used: {latest_date}",
        "- Rows after the requested analysis date are excluded before verification.",
        "",
        "### Latest verified OHLCV row",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    for field in ("Open", "High", "Low", "Close", "Volume"):
        lines.append(f"| {field} | {_fmt(latest.get(field))} |")

    lines += [
        "",
        "### Verified technical indicators (latest row)",
        "",
        "| Indicator | Value |",
        "|---|---:|",
    ]
    for name, value in indicator_values.items():
        lines.append(f"| {name} | {value} |")

    lines += [
        "",
        f"### Recent verified closes (last {len(recent)} rows)",
        "",
        "| Date | Close |",
        "|---|---:|",
    ]
    for _, row in recent.iterrows():
        lines.append(f"| {_fmt(row['Date'])} | {_fmt(row.get('Close'))} |")

    lines += [
        "",
        "Use this snapshot as the source of truth for exact OHLCV, price-level, "
        "and indicator-value claims. If another tool output conflicts with it, "
        "flag the discrepancy rather than inventing a reconciled number. Do not "
        "claim historical validation, support/resistance bounces, or exact "
        "percentage moves unless directly supported by tool output with concrete "
        "dates and prices.",
    ]
    return "\n".join(lines)


def build_vn_verified_market_snapshot(
    symbol: str,
    as_of_date: str,
    look_back_days: int = 30,
) -> str:
    """Build verified market snapshot for VN symbol with AlgoLab -> SSI whole-series fallback."""
    canonical = normalize_symbol(symbol)

    # 1. Try AlgoLab primary
    try:
        df = get_algolab_ohlcv(canonical, as_of_date, look_back_days=300)
        return render_vn_market_snapshot(df, canonical, as_of_date, look_back_days)
    except (VendorUnavailableError, NoMarketDataError) as exc:
        logger.warning("AlgoLab snapshot failed for %s: %s; falling back to SSI.", canonical, exc)

    # 2. Try SSI fallback
    try:
        df = get_ssi_ohlcv(canonical, as_of_date, look_back_days=300)
        return render_vn_market_snapshot(df, canonical, as_of_date, look_back_days)
    except Exception as exc:
        raise VendorUnavailableError(
            f"All Vietnam market data vendors (AlgoLab, SSI) failed for snapshot: {exc}"
        ) from exc
