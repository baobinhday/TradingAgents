import logging

import pandas as pd

from tradingagents.dataflows.config import get_config
from tradingagents.dataflows.errors import (
    NoMarketDataError,
    VendorNotConfiguredError,
    VendorUnavailableError,
)
from tradingagents.dataflows.vendors.algolab.fundamentals import (
    get_balance_sheet as get_algolab_balance_sheet,
    get_cashflow as get_algolab_cashflow,
    get_company_profile as get_algolab_company_profile,
    get_fundamentals as get_algolab_fundamentals,
    get_income_statement as get_algolab_income_statement,
)
from tradingagents.dataflows.vendors.algolab.macro import (
    get_macro_indicators as get_algolab_macro_indicators,
)
from tradingagents.dataflows.vendors.algolab.market import (
    get_closes as get_algolab_closes,
    get_stock_data as get_algolab_stock,
)
from tradingagents.dataflows.vendors.algolab.news import (
    get_global_news as get_algolab_global_news,
    get_insider_transactions as get_algolab_insider_transactions,
    get_news as get_algolab_news,
)
from tradingagents.dataflows.vendors.alpha_vantage import (
    get_balance_sheet as get_alpha_vantage_balance_sheet,
    get_cashflow as get_alpha_vantage_cashflow,
    get_fundamentals as get_alpha_vantage_fundamentals,
    get_global_news as get_alpha_vantage_global_news,
    get_income_statement as get_alpha_vantage_income_statement,
    get_indicator as get_alpha_vantage_indicator,
    get_insider_transactions as get_alpha_vantage_insider_transactions,
    get_news as get_alpha_vantage_news,
    get_stock as get_alpha_vantage_stock,
)
from tradingagents.dataflows.vendors.fred import get_macro_data as get_fred_macro_data
from tradingagents.dataflows.vendors.polymarket import (
    get_prediction_markets as get_polymarket_prediction_markets,
)
from tradingagents.dataflows.vendors.sec_edgar import (
    get_balance_sheet as get_sec_edgar_balance_sheet,
    get_cashflow as get_sec_edgar_cashflow,
    get_income_statement as get_sec_edgar_income_statement,
)
from tradingagents.dataflows.vendors.ssi.fundamentals import (
    get_balance_sheet as get_ssi_balance_sheet,
    get_cashflow as get_ssi_cashflow,
    get_company_profile as get_ssi_company_profile,
    get_fundamentals as get_ssi_fundamentals,
    get_income_statement as get_ssi_income_statement,
)
from tradingagents.dataflows.vendors.ssi.market import (
    get_closes as get_ssi_closes,
    get_stock_data as get_ssi_stock,
)
from tradingagents.dataflows.vendors.ssi.news import (
    get_global_news as get_ssi_global_news,
    get_insider_transactions as get_ssi_insider_transactions,
    get_news as get_ssi_news,
)
from tradingagents.dataflows.vendors.vn_indicators import (
    build_vn_verified_market_snapshot,
    get_algolab_indicators,
    get_ssi_indicators,
)
from tradingagents.dataflows.vendors.yahoo.fundamentals import (
    get_balance_sheet as get_yfinance_balance_sheet,
    get_cashflow as get_yfinance_cashflow,
    get_company_profile as get_yfinance_company_profile,
    get_fundamentals as get_yfinance_fundamentals,
    get_income_statement as get_yfinance_income_statement,
    get_insider_transactions as get_yfinance_insider_transactions,
)
from tradingagents.dataflows.vendors.yahoo.market import (
    get_closes as get_yfinance_closes,
    get_stock_stats_indicators_window,
    get_YFin_data_online,
)
from tradingagents.dataflows.vendors.yahoo.news import get_global_news_yfinance, get_news_yfinance
from tradingagents.dataflows.vendors.yahoo.snapshot import (
    build_verified_market_snapshot as get_yfinance_snapshot,
)

logger = logging.getLogger(__name__)

# Tools organized by category
TOOLS_CATEGORIES = {
    "core_stock_apis": {
        "description": "OHLCV stock price data",
        "tools": [
            "get_stock_data"
        ]
    },
    "technical_indicators": {
        "description": "Technical analysis indicators",
        "tools": [
            "get_indicators"
        ]
    },
    "fundamental_data": {
        "description": "Company fundamentals",
        "tools": [
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement"
        ]
    },
    "news_data": {
        "description": "News and insider data",
        "tools": [
            "get_news",
            "get_global_news",
            "get_insider_transactions",
        ]
    },
    "macro_data": {
        "description": "Macroeconomic indicators (rates, inflation, labor, growth)",
        "tools": [
            "get_macro_indicators",
        ]
    },
    "prediction_markets": {
        "description": "Market-implied probabilities for forward-looking events",
        "tools": [
            "get_prediction_markets",
        ]
    }
}

# Optional enrichment categories. These add macro/event context to the news
# analyst but are not core to a decision, so a vendor failure here degrades to a
# sentinel instead of aborting the run (a bad LLM-supplied indicator, a missing
# key, or a network blip should not crash an analysis over flavour data). Core
# categories (prices, fundamentals, news) still raise so a broken primary is loud.
OPTIONAL_CATEGORIES = {"macro_data", "prediction_markets"}

CO_SOURCED_METHODS = {
    "get_fundamentals",
    "get_balance_sheet",
    "get_cashflow",
    "get_income_statement",
    "get_news",
    "get_global_news",
    "get_insider_transactions",
    "get_macro_indicators",
}

# Mapping of methods to their vendor-specific implementations
VENDOR_METHODS = {
    # core_stock_apis
    "get_stock_data": {
        "alpha_vantage": get_alpha_vantage_stock,
        "yfinance": get_YFin_data_online,
        "algolab": get_algolab_stock,
        "ssi": get_ssi_stock,
    },
    # technical_indicators
    "get_indicators": {
        "alpha_vantage": get_alpha_vantage_indicator,
        "yfinance": get_stock_stats_indicators_window,
        "algolab": get_algolab_indicators,
        "ssi": get_ssi_indicators,
    },
    # fundamental_data
    "get_fundamentals": {
        "alpha_vantage": get_alpha_vantage_fundamentals,
        "yfinance": get_yfinance_fundamentals,
        "algolab": get_algolab_fundamentals,
        "ssi": get_ssi_fundamentals,
    },
    "get_balance_sheet": {
        "alpha_vantage": get_alpha_vantage_balance_sheet,
        "sec_edgar": get_sec_edgar_balance_sheet,
        "yfinance": get_yfinance_balance_sheet,
        "algolab": get_algolab_balance_sheet,
        "ssi": get_ssi_balance_sheet,
    },
    "get_cashflow": {
        "alpha_vantage": get_alpha_vantage_cashflow,
        "sec_edgar": get_sec_edgar_cashflow,
        "yfinance": get_yfinance_cashflow,
        "algolab": get_algolab_cashflow,
        "ssi": get_ssi_cashflow,
    },
    "get_income_statement": {
        "alpha_vantage": get_alpha_vantage_income_statement,
        "sec_edgar": get_sec_edgar_income_statement,
        "yfinance": get_yfinance_income_statement,
        "algolab": get_algolab_income_statement,
        "ssi": get_ssi_income_statement,
    },
    # news_data
    "get_news": {
        "alpha_vantage": get_alpha_vantage_news,
        "yfinance": get_news_yfinance,
        "algolab": get_algolab_news,
        "ssi": get_ssi_news,
    },
    "get_global_news": {
        "yfinance": get_global_news_yfinance,
        "alpha_vantage": get_alpha_vantage_global_news,
        "algolab": get_algolab_news if False else get_algolab_global_news,
        "ssi": get_ssi_global_news,
    },
    "get_insider_transactions": {
        "alpha_vantage": get_alpha_vantage_insider_transactions,
        "yfinance": get_yfinance_insider_transactions,
        "algolab": get_algolab_insider_transactions,
        "ssi": get_ssi_insider_transactions,
    },
    # macro_data
    "get_macro_indicators": {
        "fred": get_fred_macro_data,
        "algolab": get_algolab_macro_indicators,
        "ssi": get_algolab_macro_indicators,
    },
    # prediction_markets
    "get_prediction_markets": {
        "polymarket": get_polymarket_prediction_markets,
    },
}


def get_category_for_method(method: str) -> str:
    """Get the category that contains the specified method."""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"Method '{method}' not found in any category")


def get_vendor(category: str, method: str = None) -> str:
    """Get the configured vendor for a data category or specific tool method.
    Tool-level configuration takes precedence over category-level.
    Market-aware: when market is 'VN', uses vn_tool_vendors / vn_data_vendors.
    """
    config = get_config()
    market = (config.get("market") or "US").upper()

    if market == "VN":
        if method:
            vn_tool_vendors = config.get("vn_tool_vendors", {})
            if method in vn_tool_vendors:
                return vn_tool_vendors[method]
        vn_data_vendors = config.get("vn_data_vendors", {})
        if category in vn_data_vendors:
            return vn_data_vendors[category]
        return "algolab,ssi"

    # Check tool-level configuration first (if method provided)
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # Fall back to category-level configuration
    return config.get("data_vendors", {}).get(category, "default")


def vendor_unavailable(method: str, error: Exception) -> str:
    """What a call returns when every vendor was throttled or unreachable."""
    return (
        f"DATA_UNAVAILABLE: no configured vendor could serve {method} right now "
        f"({error}). This says nothing about the instrument; report the "
        f"data as unavailable and do not estimate or fabricate values."
    )


def no_data_available(error: NoMarketDataError) -> str:
    """What a call returns when every vendor that answered had no usable data."""
    resolved = "" if error.canonical == error.symbol else f" (resolved to '{error.canonical}')"
    # Surface the typed error's detail (e.g. "latest row is 2025-06-11 ...
    # stale") so the agent sees the specific reason — invalid symbol, no
    # coverage, or stale data — not just a generic "unavailable".
    reason = f" ({error.detail})" if error.detail else ""
    return (
        f"NO_DATA_AVAILABLE: No usable market data for '{error.symbol}'{resolved} from "
        f"any configured vendor{reason}. The symbol may be invalid, delisted, "
        f"not covered, or the vendor returned stale data. Do not estimate or "
        f"fabricate values — report that data is unavailable for this symbol."
    )


def _deduplicate_news_markdown(primary_md: str, secondary_md: str) -> str:
    """Remove articles from secondary_md whose title or link is in primary_md."""
    seen_titles = set()
    seen_links = set()
    for line in primary_md.splitlines():
        line = line.strip()
        if line.startswith("### "):
            title = line[4:].split(" (source:")[0].strip().lower()
            if title:
                seen_titles.add(title)
        elif line.startswith("Link: "):
            link = line[6:].strip().lower()
            if link:
                seen_links.add(link)

    blocks = secondary_md.split("### ")
    kept_blocks = [blocks[0]]
    for block in blocks[1:]:
        lines = block.splitlines()
        first_line = lines[0].strip()
        title = first_line.split(" (source:")[0].strip().lower()
        block_link = ""
        for bl in lines:
            if bl.strip().startswith("Link: "):
                block_link = bl.strip()[6:].strip().lower()
                break
        if (title and title in seen_titles) or (block_link and block_link in seen_links):
            continue
        kept_blocks.append(block)

    return "### ".join(kept_blocks)


def _co_source_vn_vendors(method: str, vendor_chain: list[str], *args, **kwargs) -> str:
    """Side-by-side multi-source aggregation for non-price Vietnam market data."""
    results: dict[str, str] = {}
    errors: dict[str, Exception] = {}

    for vendor in vendor_chain:
        vendor_dict = VENDOR_METHODS.get(method, {})
        impl = vendor_dict.get(vendor)
        if not impl:
            continue
        try:
            res = impl(*args, **kwargs)
            if res and isinstance(res, str):
                results[vendor] = res
        except (VendorUnavailableError, VendorNotConfiguredError, NoMarketDataError) as exc:
            logger.warning("Vendor %r in co-sourcing for %s failed: %s", vendor, method, exc)
            errors[vendor] = exc
        except Exception as exc:
            logger.warning("Vendor %r in co-sourcing for %s unexpected failure: %s", vendor, method, exc)
            errors[vendor] = exc

    if not results:
        if any(isinstance(e, NoMarketDataError) for e in errors.values()):
            first_no_data = next(e for e in errors.values() if isinstance(e, NoMarketDataError))
            return no_data_available(first_no_data)
        if errors:
            first_err = next(iter(errors.values()))
            category = get_category_for_method(method)
            if category in OPTIONAL_CATEGORIES:
                return (
                    f"DATA_UNAVAILABLE: optional {category} could not be retrieved "
                    f"({first_err}). Proceed without it; do not fabricate values."
                )
            return vendor_unavailable(method, first_err)
        raise VendorUnavailableError(f"No configured vendor succeeded for co-sourced {method}")

    if len(results) == 1 and not errors:
        return next(iter(results.values()))

    # Apply news deduplication if both succeeded
    if method in ("get_news", "get_global_news") and "algolab" in results and "ssi" in results:
        results["ssi"] = _deduplicate_news_markdown(results["algolab"], results["ssi"])

    output_parts = []
    for vendor, text in results.items():
        v_title = "AlgoLab" if vendor == "algolab" else "SSI" if vendor == "ssi" else vendor.upper()
        output_parts.append(f"### [Source: {v_title}]\n{text}")

    for vendor, err in errors.items():
        v_title = "AlgoLab" if vendor == "algolab" else "SSI" if vendor == "ssi" else vendor.upper()
        output_parts.append(f"> [!NOTE]\n> Source '{v_title}' unavailable: {err}")

    return "\n\n".join(output_parts)


def route_to_vendor(method: str, *args, **kwargs):
    """Route method calls to appropriate vendor implementation with fallback support."""
    config = get_config()
    market = (config.get("market") or "US").upper()
    if args and isinstance(args[0], str) and args[0].upper().endswith(".VN"):
        market = "VN"

    category = get_category_for_method(method)
    vendor_config = get_vendor(category, method)
    primary_vendors = [v.strip() for v in vendor_config.split(',') if v.strip()]

    if method not in VENDOR_METHODS:
        raise ValueError(f"Method '{method}' not supported")

    all_available_vendors = list(VENDOR_METHODS[method].keys())

    # Disabled category for this market (e.g. prediction_markets for VN)
    if primary_vendors == ["none"]:
        if category in OPTIONAL_CATEGORIES:
            return (
                f"DATA_UNAVAILABLE: optional {category} is not configured for market {market}. "
                f"Proceed without it; do not fabricate values."
            )
        raise VendorUnavailableError(f"Category '{category}' is disabled for market {market}")

    # The configured vendor list IS the chain: we do NOT silently fall back to
    # vendors the user did not choose (#988/#289) — that returned data from an
    # unexpected source and caused cross-vendor inconsistencies. For multi-vendor
    # fallback, list them in order, e.g. data_vendors="yfinance,alpha_vantage".
    # The "default" sentinel (no explicit config) uses all available vendors.
    explicit = [v for v in primary_vendors if v and v != "default" and v != "none"]
    if explicit:
        vendor_chain = [v for v in explicit if v in VENDOR_METHODS[method]]
        if not vendor_chain:
            raise ValueError(
                f"Configured vendor(s) {explicit} not available for '{method}'. "
                f"Available: {all_available_vendors}."
            )
    else:
        vendor_chain = all_available_vendors

    # Strict enforcement: under NO circumstances may Yahoo / yfinance be called for market VN
    if market == "VN":
        vendor_chain = [v for v in vendor_chain if v not in ("yfinance", "yahoo")]
        if not vendor_chain:
            vendor_chain = [v for v in ("algolab", "ssi") if v in VENDOR_METHODS[method]]

    # Multi-source co-sourcing for Vietnam non-price categories
    if market == "VN" and method in CO_SOURCED_METHODS and len(vendor_chain) > 1:
        return _co_source_vn_vendors(method, vendor_chain, *args, **kwargs)

    last_no_data: NoMarketDataError | None = None
    last_unavailable: VendorUnavailableError | None = None
    failed: Exception | None = None     # a vendor that raised something untyped
    first_error: Exception | None = None
    for vendor in vendor_chain:
        vendor_impl = VENDOR_METHODS[method][vendor]
        impl_func = vendor_impl[0] if isinstance(vendor_impl, list) else vendor_impl

        try:
            return impl_func(*args, **kwargs)
        except VendorUnavailableError as e:
            logger.warning("Vendor %r unavailable for %s: %s; trying next vendor.", vendor, method, e)
            # Kept so an all-unavailable chain can say the vendor was the
            # problem, rather than reporting nothing about the symbol.
            last_unavailable = e
            continue
        except VendorNotConfiguredError as e:
            logger.warning("Vendor %r not configured for %s; trying next vendor.", vendor, method)
            if first_error is None:
                first_error = e  # Surface it if no other vendor can serve the call.
            continue
        except NoMarketDataError as e:
            last_no_data = e  # No data here; another configured vendor may have it
            continue
        except Exception as e:
            # Don't let one vendor's failure crash the call when another can
            # serve it, but never swallow silently: a broken primary must be
            # visible in the logs (#989), not hidden behind a fallback's verdict.
            logger.warning("Vendor %r failed for %s: %s", vendor, method, e)
            if first_error is None:
                first_error = e
            failed = e
            continue

    # A vendor that throttled or failed the request never said whether it has
    # the symbol, so no other vendor's "no data" can speak for the whole chain:
    # report the vendors as the problem, not the instrument. It must not end
    # the run either.
    if last_unavailable is not None:
        return vendor_unavailable(method, last_unavailable)
    if failed is not None and last_no_data is not None:
        return vendor_unavailable(method, failed)

    # Every vendor that answered reported "no data": the symbol is genuinely unavailable.
    # Return one explicit, instructive sentinel rather than a vendor-specific
    # empty string, so the agent reports "unavailable" instead of inventing a
    # value. This takes precedence over incidental fallback errors.
    if last_no_data is not None:
        if first_error is not None:
            # A vendor also hit a real error; surface it in logs so the no-data
            # verdict can't hide a broken primary (network/auth/etc.).
            logger.warning(
                "Returning NO_DATA for %s, but a vendor errored earlier: %s",
                method, first_error,
            )
        return no_data_available(last_no_data)

    # No vendor returned data and none reported clean "no data" — surface the
    # first real error (e.g. the primary vendor's network failure). Optional
    # enrichment categories degrade to a sentinel instead, so flavour data can't
    # abort the run.
    if first_error is not None:
        if category in OPTIONAL_CATEGORIES:
            logger.warning("Optional %s unavailable for %s: %s", category, method, first_error)
            return (
                f"DATA_UNAVAILABLE: optional {category} could not be retrieved "
                f"({first_error}). Proceed without it; do not fabricate values."
            )
        raise first_error

    raise RuntimeError(f"No available vendor for '{method}'")


def get_closes(symbol: str, start_date: str, end_date: str, market: str | None = None) -> pd.Series:
    """Daily closes from start_date up to, not including, end_date.

    Market-aware: When market is 'VN' (or symbol ends with '.VN'), routes to VN vendors
    (AlgoLab primary -> SSI fallback) and never calls Yahoo Finance.
    """
    config = get_config()
    target_market = (market or config.get("market", "US")).upper()
    if target_market == "VN" or symbol.upper().endswith(".VN"):
        try:
            s = get_algolab_closes(symbol, start_date, end_date)
            if s is not None and not s.empty:
                return s
        except Exception as e:
            logger.warning("AlgoLab get_closes failed for %s: %s; trying SSI fallback", symbol, e)
        try:
            s = get_ssi_closes(symbol, start_date, end_date)
            if s is not None and not s.empty:
                return s
        except Exception as e:
            logger.warning("SSI get_closes failed for %s: %s", symbol, e)
        raise VendorUnavailableError(f"Vietnam market vendor (AlgoLab / SSI) could not provide closes for {symbol}")
    return get_yfinance_closes(symbol, start_date, end_date)


def get_company_profile(ticker: str, market: str | None = None) -> dict:
    """Resolve company identity metadata via configured vendor.

    Market-aware: When market is 'VN' (or ticker ends with '.VN'), routes to VN vendors
    (AlgoLab primary -> SSI fallback) and never calls Yahoo Finance.
    """
    config = get_config()
    target_market = (market or config.get("market", "US")).upper()
    if target_market == "VN" or ticker.upper().endswith(".VN"):
        try:
            p = get_algolab_company_profile(ticker)
            if p:
                return p
        except Exception as e:
            logger.warning("AlgoLab get_company_profile failed for %s: %s; trying SSI fallback", ticker, e)
        try:
            p = get_ssi_company_profile(ticker)
            if p:
                return p
        except Exception as e:
            logger.warning("SSI get_company_profile failed for %s: %s", ticker, e)
        raise VendorUnavailableError(f"Vietnam market vendor (AlgoLab / SSI) could not resolve profile for {ticker}")
    return get_yfinance_company_profile(ticker)


def get_verified_market_snapshot(symbol: str, as_of_date: str, look_back_days: int = 30) -> str:
    """Market-aware verification snapshot for exact market-data claims.

    Routes by market:
    - VN: routes to VN vendors without touching Yahoo.
    - US / default: generates verified snapshot from vendor OHLCV.
    """
    config = get_config()
    target_market = (config.get("market") or "US").upper()
    if target_market == "VN" or symbol.upper().endswith(".VN"):
        try:
            return build_vn_verified_market_snapshot(symbol, as_of_date, look_back_days)
        except Exception as exc:
            return vendor_unavailable("get_verified_market_snapshot", exc)
    return get_yfinance_snapshot(symbol, as_of_date, look_back_days)
