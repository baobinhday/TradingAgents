"""AlgoLab Macroeconomic Indicators Adapter."""

from __future__ import annotations

import logging

import pandas as pd

from tradingagents.dataflows.vendors.algolab.client import AlgoLabClient

logger = logging.getLogger(__name__)


def get_macro_indicators(
    indicator: str = "all",
    as_of_date: str | None = None,
    look_back_days: int = 30,
) -> str:
    """Retrieve Vietnam macroeconomic indicators (CPI, GDP, M2, FX, IIP, etc.) from AlgoLab."""
    client = AlgoLabClient.get_instance()

    res = client.call_tool("get_macro", {"scope": "vietnam", "limit": 10})
    data = res.get("data", {}) if isinstance(res, dict) else {}
    series = data.get("series") if isinstance(data, dict) else None

    if not series:
        return "DATA_UNAVAILABLE: no macroeconomic series returned by AlgoLab"

    if isinstance(series, dict) and "columns" in series and "rows" in series:
        df = pd.DataFrame(series["rows"], columns=series["columns"])
    elif isinstance(series, list):
        df = pd.DataFrame(series)
    else:
        return str(series)

    if df.empty:
        return "DATA_UNAVAILABLE: empty macroeconomic series returned by AlgoLab"

    lines = ["## Vietnam Macroeconomic Indicators\n"]
    lines.append("| Symbol | Indicator Name | Latest Date | Latest Value | Previous Date | Previous Value | Unit |")
    lines.append("|---|---|---|---|---|---|---|")

    for _, row in df.iterrows():
        sym = row.get("symbol", "")
        name = row.get("name", "")
        l_date = row.get("latest.date", "")
        l_val = row.get("latest.value", "")
        p_date = row.get("previous.date", "")
        p_val = row.get("previous.value", "")
        unit = row.get("unit", "")
        lines.append(f"| {sym} | {name} | {l_date} | {l_val} | {p_date} | {p_val} | {unit} |")

    return "\n".join(lines)
