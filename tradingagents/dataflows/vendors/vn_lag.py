"""Simulated statutory reporting lag for Vietnamese financial statements.

In Vietnam equity markets, financial statements do not carry publication
timestamps from data vendors (AlgoLab, SSI). Under statutory regulations
(Circular 96/2020/TT-BTC):
- Quarterly financial statements (Q1, Q2, Q3, Q4) must be disclosed within
  45 days following the quarter end.
- Annual financial statements (FY) must be disclosed within 90 days following
  the fiscal year end (December 31).

To eliminate lookahead bias in historical backtests and dated analysis, this
module calculates the simulated statutory publication date for each reporting
period and filters out statements that were not yet published on or before
the requested as_of_date.
"""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Statutory reporting lag in days
QUARTERLY_LAG_DAYS = 45
ANNUAL_LAG_DAYS = 90


def get_vn_period_publication_date(period_repr: Any) -> str | None:
    """Calculate the simulated statutory publication date (YYYY-MM-DD) for a period.

    Accepts:
    - String representations: '2024-Q1', '2024Q1', 'Q1/2024', 'Q1 2024', '2024-1',
      '2024' (annual), 'FY2024', '2024-FY', '2024-03-31'
    - Dict representations: {'year_report': 2024, 'length_report': 1}
      (where length_report: 1..4 = Q1..Q4, 5 = Annual/FY, 6 = H1, 9 = 9M)
    - Returns None if the input cannot be identified as a reporting period
      (e.g., metric/item names like 'revenue', 'item', 'Chỉ tiêu').
    """
    if period_repr is None:
        return None

    year: int | None = None
    quarter: int | None = None  # 1..4, or None for annual

    # Handle dictionary representation (SSI and structured records)
    if isinstance(period_repr, dict):
        y_val = (
            period_repr.get("year_report")
            or period_repr.get("yearReport")
            or period_repr.get("year")
            or period_repr.get("YearReport")
        )
        l_val = (
            period_repr.get("length_report")
            or period_repr.get("lengthReport")
            or period_repr.get("quarter")
            or period_repr.get("LengthReport")
        )
        if y_val is not None:
            try:
                year = int(y_val)
            except (ValueError, TypeError):
                return None
        if l_val is not None:
            try:
                l_int = int(l_val)
                if l_int in (1, 2, 3, 4):
                    quarter = l_int
                elif l_int == 5:
                    quarter = None  # Full year / Annual
                elif l_int == 6:
                    quarter = 2  # H1 (ends 06-30)
                elif l_int == 9:
                    quarter = 3  # 9M (ends 09-30)
            except (ValueError, TypeError):
                pass
        if year is not None:
            return _calculate_pub_date(year, quarter)
        return None

    s = str(period_repr).strip()
    if not s:
        return None

    # Check for quarter patterns: '2024-Q1', '2024Q1', '2024_Q1', '2024/Q1'
    m_q1 = re.search(r"(\d{4})[-_\s/.]*[Qq](\d)", s)
    if m_q1:
        year = int(m_q1.group(1))
        quarter = int(m_q1.group(2))
        return _calculate_pub_date(year, quarter)

    # Check for quarter patterns: 'Q1/2024', 'Q1-2024', 'Q1 2024'
    m_q2 = re.search(r"[Qq](\d)[-_\s/.]*(\d{4})", s)
    if m_q2:
        quarter = int(m_q2.group(1))
        year = int(m_q2.group(2))
        return _calculate_pub_date(year, quarter)

    # Check for numeric quarter: '2024-1', '2024/2', etc.
    m_q3 = re.search(r"^(\d{4})[-_/]([1-4])$", s)
    if m_q3:
        year = int(m_q3.group(1))
        quarter = int(m_q3.group(2))
        return _calculate_pub_date(year, quarter)

    # Check for date: '2024-03-31', '2024-06-30', '2024-09-30', '2024-12-31'
    m_date = re.search(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m_date:
        year = int(m_date.group(1))
        month = int(m_date.group(2))
        if month in (1, 2, 3):
            quarter = 1
        elif month in (4, 5, 6):
            quarter = 2
        elif month in (7, 8, 9):
            quarter = 3
        elif month in (10, 11, 12):
            quarter = 4
        return _calculate_pub_date(year, quarter)

    # Check for annual year: '2024', 'FY2024', '2024-FY', 'FY 2024'
    m_yr = re.search(r"^(?:FY)?\s*(\d{4})\s*(?:FY)?$", s, re.IGNORECASE)
    if m_yr:
        year = int(m_yr.group(1))
        # Ensure it is a plausible calendar year
        if 1990 <= year <= 2100:
            return _calculate_pub_date(year, quarter=None)

    return None


def _calculate_pub_date(year: int, quarter: int | None) -> str:
    """Calculate publication date from year and quarter."""
    if quarter == 1:
        end_date = date(year, 3, 31)
        pub_date = end_date + timedelta(days=QUARTERLY_LAG_DAYS)
    elif quarter == 2:
        end_date = date(year, 6, 30)
        pub_date = end_date + timedelta(days=QUARTERLY_LAG_DAYS)
    elif quarter == 3:
        end_date = date(year, 9, 30)
        pub_date = end_date + timedelta(days=QUARTERLY_LAG_DAYS)
    elif quarter == 4:
        end_date = date(year, 12, 31)
        pub_date = end_date + timedelta(days=QUARTERLY_LAG_DAYS)
    else:
        # Annual report: 90 days post FY-end (Dec 31)
        end_date = date(year, 12, 31)
        pub_date = end_date + timedelta(days=ANNUAL_LAG_DAYS)

    return pub_date.strftime("%Y-%m-%d")


def is_period_published(period_repr: Any, as_of_date: str | None) -> bool:
    """Check if a reporting period's publication date is on or before as_of_date.

    If as_of_date is None or empty, returns True.
    If period_repr is not a period (e.g. metadata/item column), returns True.
    Otherwise returns (pub_date <= as_of_date).
    """
    if not as_of_date:
        return True
    pub_date = get_vn_period_publication_date(period_repr)
    if pub_date is None:
        # Not a period indicator; keep it
        return True
    return pub_date <= str(as_of_date)


def filter_algolab_statements_by_lag(
    lines_data: Any, as_of_date: str | None
) -> tuple[Any, int]:
    """Filter AlgoLab statement lines by simulated publication lag.

    Returns (filtered_lines_data, dropped_period_count).
    Supports dictionary format with 'columns' and 'rows', or list format.
    """
    if not as_of_date or not lines_data:
        return lines_data, 0

    dropped_count = 0

    if isinstance(lines_data, dict) and "columns" in lines_data and "rows" in lines_data:
        columns = lines_data["columns"]
        rows = lines_data["rows"]

        kept_indices = []
        for idx, col in enumerate(columns):
            pub_date = get_vn_period_publication_date(col)
            if pub_date is None:
                # Keep non-period columns (e.g. item, code, name)
                kept_indices.append(idx)
            elif pub_date <= as_of_date:
                kept_indices.append(idx)
            else:
                dropped_count += 1
                logger.debug(
                    "Dropping unpublished column %s (pub_date %s > as_of_date %s)",
                    col,
                    pub_date,
                    as_of_date,
                )

        new_columns = [columns[i] for i in kept_indices]
        new_rows = []
        for row in rows:
            new_rows.append([row[i] for i in kept_indices if i < len(row)])

        return {"columns": new_columns, "rows": new_rows}, dropped_count

    if isinstance(lines_data, list):
        filtered_list = []
        for item in lines_data:
            if isinstance(item, dict):
                pub_date = get_vn_period_publication_date(item)
                if pub_date is None or pub_date <= as_of_date:
                    filtered_list.append(item)
                else:
                    dropped_count += 1
            else:
                filtered_list.append(item)
        return filtered_list, dropped_count

    return lines_data, 0


def filter_ssi_statements_by_lag(
    items: list[dict[str, Any]], as_of_date: str | None
) -> list[dict[str, Any]]:
    """Filter SSI statement records by simulated publication lag.

    Drops records where simulated publication date > as_of_date.
    """
    if not as_of_date or not items:
        return items

    filtered = []
    for item in items:
        pub_date = get_vn_period_publication_date(item)
        if pub_date is None or pub_date <= as_of_date:
            filtered.append(item)
        else:
            logger.debug(
                "Dropping unpublished SSI record %s/%s (pub_date %s > as_of_date %s)",
                item.get("year_report") or item.get("yearReport"),
                item.get("length_report") or item.get("lengthReport"),
                pub_date,
                as_of_date,
            )

    return filtered
