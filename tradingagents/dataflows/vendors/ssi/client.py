"""SSI MCP Streamable HTTP POST Transport Client with OAuth Token Rotation and Rate Limiting."""

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

SSI_MCP_BASE = os.getenv("SSI_MCP_BASE", "https://mcp.ssi.com.vn")
SSI_MCP_URL = f"{SSI_MCP_BASE}/mcp"
SSI_TOKEN_URL = f"{SSI_MCP_BASE}/oauth/token"

PRIMARY_TOKEN_FILE = Path.home() / ".tradingagents" / "ssi_tokens.json"
FALLBACK_TOKEN_FILE = Path("scripts/spike_mcp/.ssi_auth_cache.json")


class SSITokenManager:
    """Manages SSI OAuth tokens with unattended single-use Refresh Token Rotation (RFC 6749 §6)."""

    def __init__(self, primary_path: Path = PRIMARY_TOKEN_FILE, fallback_path: Path = FALLBACK_TOKEN_FILE):
        self.primary_path = primary_path
        self.fallback_path = fallback_path
        self._lock = threading.Lock()
        self._active_file: Path | None = None
        self._cached_auth: dict[str, Any] | None = None

    def _read_cache(self) -> dict[str, Any] | None:
        """Read token data from primary or fallback cache file."""
        for path in (self.primary_path, self.fallback_path):
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "tokens" in data:
                        tokens = data.get("tokens", {})
                        if tokens.get("access_token"):
                            self._active_file = path
                            return data
                except Exception as exc:
                    logger.debug("Failed reading SSI token cache from %s: %s", path, exc)
        return None

    def _write_cache(self, auth_data: dict[str, Any]) -> None:
        """Atomically persist rotated tokens."""
        target_files = []
        if self._active_file:
            target_files.append(self._active_file)
        if self.primary_path not in target_files:
            target_files.append(self.primary_path)

        for target in target_files:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                temp_file = target.with_suffix(".tmp")
                temp_file.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")
                temp_file.replace(target)
                self._active_file = target
            except Exception as exc:
                logger.error("Failed saving rotated SSI tokens to %s: %s", target, exc)

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Get valid access token, auto-refreshing if expired or force_refresh is True."""
        with self._lock:
            if not self._cached_auth or force_refresh:
                self._cached_auth = self._read_cache()

            if not self._cached_auth:
                raise VendorNotConfiguredError(
                    "SSI MCP authentication tokens not found. Please authenticate via scripts/spike_mcp/spike_ssi.py "
                    f"to create {self.primary_path} or {self.fallback_path}."
                )

            tokens = self._cached_auth.get("tokens", {})
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            client_id = self._cached_auth.get("client_id")

            # Check if access token is near expiration (within 60s)
            created_at = self._cached_auth.get("refreshed_at") or self._cached_auth.get("created_at") or 0
            expires_in = tokens.get("expires_in", 2592000)  # default 30 days
            is_expired = (time.time() - created_at) > (expires_in - 60) if created_at else False

            if force_refresh or is_expired:
                if not refresh_token or not client_id:
                    if access_token and not force_refresh:
                        return access_token
                    raise VendorNotConfiguredError(
                        "SSI MCP refresh token or client_id missing. Please re-authenticate."
                    )
                access_token = self._refresh_tokens(client_id, refresh_token)

            return access_token

    def _refresh_tokens(self, client_id: str, refresh_token: str) -> str:
        """Execute single-use refresh token exchange and immediately persist new tokens."""
        logger.info("Refreshing SSI MCP access token via RFC 6749 refresh grant...")
        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(SSI_TOKEN_URL, data=payload)
        except Exception as exc:
            raise VendorUnavailableError(f"SSI OAuth token refresh request failed: {exc}") from exc

        if res.status_code == 200:
            new_tokens = res.json()
            if self._cached_auth is None:
                self._cached_auth = {}
            self._cached_auth["client_id"] = client_id
            self._cached_auth["tokens"] = new_tokens
            self._cached_auth["refreshed_at"] = time.time()
            self._write_cache(self._cached_auth)
            logger.info("SSI MCP token refresh successful and rotated tokens saved to disk.")
            return new_tokens["access_token"]
        elif res.status_code in (400, 401):
            err_data = res.text
            raise VendorNotConfiguredError(
                f"SSI refresh token invalid or revoked (HTTP {res.status_code}: {err_data}). "
                "Please run scripts/spike_mcp/spike_ssi.py to re-authenticate."
            )
        else:
            raise VendorUnavailableError(
                f"SSI token refresh failed with HTTP {res.status_code}: {res.text[:100]}"
            )


class SSIMCPClient:
    """Thread-safe client for SSI MCP server with rate limiting, token refresh, and caching."""

    _instance: SSIMCPClient | None = None
    _singleton_lock = threading.Lock()

    def __init__(self, token_manager: SSITokenManager | None = None, timeout: float = 35.0):
        self.token_manager = token_manager or SSITokenManager()
        self.timeout = timeout
        self._req_id = 0
        self._req_id_lock = threading.Lock()
        self._rate_lock = threading.Lock()
        self._last_request_time = 0.0
        self._min_interval = 0.5  # ~2 requests per second
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_lock = threading.Lock()
        self._default_ttl = 300  # 5 minutes TTL

    @classmethod
    def get_instance(cls) -> SSIMCPClient:
        """Get or initialize singleton instance."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _next_id(self) -> int:
        with self._req_id_lock:
            self._req_id += 1
            return self._req_id

    def _throttle(self) -> None:
        """Enforce ~2 req/s rate limit pacing."""
        with self._rate_lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request_time = time.time()

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

    def call_rpc(self, method: str, params: dict | None = None, retry_count: int = 0) -> dict[str, Any]:
        """Send JSON-RPC call over Streamable HTTP POST and parse SSE event stream with auto-retry."""
        token = self.token_manager.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }

        self._throttle()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(SSI_MCP_URL, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise VendorUnavailableError(f"SSI MCP request timed out after {self.timeout}s: {exc}") from exc
        except httpx.NetworkError as exc:
            raise VendorUnavailableError(f"SSI MCP network error: {exc}") from exc
        except Exception as exc:
            raise VendorUnavailableError(f"SSI MCP HTTP request failed: {exc}") from exc

        # Handle 401 Unauthorized by rotating token and retrying once
        if res.status_code == 401 and retry_count == 0:
            logger.info("SSI MCP returned 401 Unauthorized; attempting token refresh...")
            self.token_manager.get_access_token(force_refresh=True)
            return self.call_rpc(method, params, retry_count=retry_count + 1)

        if res.status_code == 429:
            if retry_count < 3:
                time.sleep(2.0 * (retry_count + 1))
                return self.call_rpc(method, params, retry_count=retry_count + 1)
            raise VendorUnavailableError("SSI MCP rate limit exceeded (HTTP 429).")

        if res.status_code in (401, 403):
            raise VendorUnavailableError(
                f"SSI MCP rejected authentication (HTTP {res.status_code}). Please verify tokens."
            )
        if res.status_code >= 500:
            raise VendorUnavailableError(f"SSI MCP server error (HTTP {res.status_code}): {res.text[:100]}")

        # Parse SSE lines for data: {...}
        text = res.text
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                try:
                    return json.loads(line[6:])
                except json.JSONDecodeError as exc:
                    raise VendorUnavailableError(f"Malformed JSON in SSI SSE response: {exc}") from exc

        try:
            return res.json()
        except Exception:
            raise VendorUnavailableError(f"SSI MCP response contained no SSE data line: {text[:200]}") from None

    def call_tool(self, name: str, arguments: dict[str, Any], use_cache: bool = True) -> Any:
        """Call an MCP tool on SSI and unwrap the result."""
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
            if "not found" in msg.lower() or "invalid symbol" in msg.lower():
                raise NoMarketDataError(
                    symbol=arguments.get("symbol") or arguments.get("indexCode", ""),
                    canonical=arguments.get("symbol") or arguments.get("indexCode", ""),
                    detail=f"SSI error: {msg}",
                )
            raise VendorUnavailableError(f"SSI MCP error ({code}): {msg}")

        result = rpc_res.get("result", {})
        if result.get("isError"):
            content = result.get("content", [])
            err_msg = content[0].get("text") if content else "Tool returned error flag"
            err_str = str(err_msg).lower()
            if "not found" in err_str or "invalid symbol" in err_str:
                raise NoMarketDataError(
                    symbol=arguments.get("symbol") or arguments.get("indexCode", ""),
                    canonical=arguments.get("symbol") or arguments.get("indexCode", ""),
                    detail=str(err_msg),
                )
            raise VendorUnavailableError(f"SSI tool '{name}' failed: {err_msg}")

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

        if isinstance(parsed, dict) and parsed.get("status") == "error":
            err = parsed.get("error", {})
            code = err.get("code")
            msg = err.get("message") or str(err)
            if code in ("SYMBOL_NOT_FOUND", "DATA_NOT_FOUND") or "not found" in msg.lower():
                raise NoMarketDataError(
                    symbol=arguments.get("symbol") or arguments.get("indexCode", ""),
                    canonical=arguments.get("symbol") or arguments.get("indexCode", ""),
                    detail=msg,
                )
            if code == "RATE_LIMITED":
                retry_sec = err.get("retryAfterSeconds", 2)
                time.sleep(retry_sec)
                return self.call_tool(name, arguments, use_cache=False)
            raise VendorUnavailableError(f"SSI error ({code}): {msg}")

        if use_cache and parsed is not None:
            self._set_cached(cache_key, parsed)

        return parsed
