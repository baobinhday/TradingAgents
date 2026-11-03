"""AlgoLab MCP Streamable HTTP POST Client with caching and rate protection."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

import httpx

from tradingagents.dataflows.errors import (
    NoMarketDataError,
    VendorNotConfiguredError,
    VendorUnavailableError,
)

logger = logging.getLogger(__name__)

ALGOLAB_MCP_URL = os.getenv("ALGOLAB_MCP_URL", "https://mcp.algolab.vn")
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 TradingAgents/1.0"
)


def get_algolab_api_key() -> str | None:
    """Retrieve ALGOLAB_API_KEY from environment or .env file without logging the value."""
    key = os.environ.get("ALGOLAB_API_KEY")
    if key and key.strip():
        return key.strip()

    env_path = Path(".env")
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("ALGOLAB_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip("\"'")
                    if val:
                        return val
        except Exception as exc:
            logger.debug("Could not read .env file for ALGOLAB_API_KEY: %s", exc)
    return None


class AlgoLabClient:
    """Thread-safe client for AlgoLab MCP server with caching and quota protection."""

    _instance: AlgoLabClient | None = None
    _lock = threading.Lock()

    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        self.api_key = api_key or get_algolab_api_key()
        self.timeout = timeout
        self._req_id = 0
        self._req_id_lock = threading.Lock()
        self._cache: dict[str, tuple[float, Any]] = {}  # key -> (timestamp, data)
        self._cache_lock = threading.Lock()
        self._default_ttl = 300  # 5 minutes in-memory TTL

    @classmethod
    def get_instance(cls) -> AlgoLabClient:
        """Get or initialize singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _next_id(self) -> int:
        with self._req_id_lock:
            self._req_id += 1
            return self._req_id

    def _get_cached(self, cache_key: str) -> Any | None:
        with self._cache_lock:
            entry = self._cache.get(cache_key)
            if entry is not None:
                cached_time, val = entry
                if time.time() - cached_time < self._default_ttl:
                    return val
                self._cache.pop(cache_key, None)
        return None

    def _set_cached(self, cache_key: str, val: Any) -> None:
        with self._cache_lock:
            self._cache[cache_key] = (time.time(), val)

    def call_rpc(self, method: str, params: dict | None = None) -> dict[str, Any]:
        """Send JSON-RPC call over Streamable HTTP POST and parse SSE event stream."""
        key = self.api_key or get_algolab_api_key()
        if not key:
            raise VendorNotConfiguredError(
                "AlgoLab API key is not configured. Set ALGOLAB_API_KEY in your environment or .env file."
            )

        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(ALGOLAB_MCP_URL, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise VendorUnavailableError(f"AlgoLab MCP request timed out after {self.timeout}s: {exc}") from exc
        except httpx.NetworkError as exc:
            raise VendorUnavailableError(f"AlgoLab MCP network error: {exc}") from exc
        except Exception as exc:
            raise VendorUnavailableError(f"AlgoLab MCP HTTP request failed: {exc}") from exc

        if res.status_code in (401, 403):
            raise VendorUnavailableError(
                f"AlgoLab MCP rejected authentication (HTTP {res.status_code}). Please verify ALGOLAB_API_KEY."
            )
        if res.status_code == 429:
            raise VendorUnavailableError("AlgoLab MCP rate limit exceeded (HTTP 429).")
        if res.status_code >= 500:
            raise VendorUnavailableError(f"AlgoLab MCP server error (HTTP {res.status_code}): {res.text[:100]}")

        # Parse SSE lines for data: {...}
        text = res.text
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                try:
                    return json.loads(line[6:])
                except json.JSONDecodeError as exc:
                    raise VendorUnavailableError(f"Malformed JSON in AlgoLab SSE response: {exc}") from exc

        # If server returned non-SSE JSON directly
        try:
            return res.json()
        except Exception:
            raise VendorUnavailableError(f"AlgoLab MCP response contained no SSE data line: {text[:200]}") from None

    def call_tool(self, name: str, arguments: dict[str, Any], use_cache: bool = True) -> Any:
        """Call an MCP tool on AlgoLab and unwrap the result."""
        cache_key = f"{name}:{json.dumps(arguments, sort_keys=True)}"
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        rpc_res = self.call_rpc("tools/call", {"name": name, "arguments": arguments})

        # Check for top-level JSON-RPC error
        if "error" in rpc_res:
            err = rpc_res["error"]
            code = err.get("code")
            msg = err.get("message", "Unknown error")
            if code == -32602 or "not found" in msg.lower():
                raise NoMarketDataError(
                    symbol=arguments.get("symbol", ""),
                    canonical=arguments.get("symbol", ""),
                    detail=f"AlgoLab error: {msg}",
                )
            raise VendorUnavailableError(f"AlgoLab MCP error ({code}): {msg}")

        result = rpc_res.get("result", {})
        if result.get("isError"):
            content = result.get("content", [])
            err_msg = content[0].get("text") if content else "Tool returned error flag"
            if "not found" in str(err_msg).lower() or "invalid symbol" in str(err_msg).lower():
                raise NoMarketDataError(
                    symbol=arguments.get("symbol", ""),
                    canonical=arguments.get("symbol", ""),
                    detail=str(err_msg),
                )
            raise VendorUnavailableError(f"AlgoLab tool '{name}' failed: {err_msg}")

        # Unwrap text content
        content = result.get("content", [])
        if not content:
            return None

        first = content[0]
        text_data = first.get("text", "")
        try:
            parsed = json.loads(text_data)
        except Exception:
            parsed = text_data

        # Inspect AlgoLab payload status if present: {status, data, meta, error}
        if isinstance(parsed, dict):
            if parsed.get("status") == "error":
                err = parsed.get("error", {})
                code = err.get("code")
                msg = err.get("message") or err.get("hint") or str(err)
                if code in ("SYMBOL_NOT_FOUND", "DATA_NOT_FOUND") or "not found" in msg.lower():
                    raise NoMarketDataError(
                        symbol=arguments.get("symbol", ""),
                        canonical=arguments.get("symbol", ""),
                        detail=msg,
                    )
                if code in ("SESSION_LIMIT", "RATE_LIMIT"):
                    raise VendorUnavailableError(f"AlgoLab quota limit reached: {msg}")
                raise VendorUnavailableError(f"AlgoLab error ({code}): {msg}")

            # Track quota in debug logs if present
            meta = parsed.get("meta")
            if isinstance(meta, dict) and "quota" in meta:
                logger.debug("AlgoLab quota remaining: %s", meta.get("quota"))

        if use_cache and parsed is not None:
            self._set_cached(cache_key, parsed)

        return parsed
