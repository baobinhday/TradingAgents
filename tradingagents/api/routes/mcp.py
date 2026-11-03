from __future__ import annotations

import base64
import hashlib
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from tradingagents.api.schemas import (
    AlgolabKeySubmitRequest,
    AlgolabStatus,
    McpStatusResponse,
    McpTestResponse,
    SsiAuthStartRequest,
    SsiAuthStartResponse,
    SsiStatus,
    SsiTokensSubmitRequest,
)
from tradingagents.dataflows.vendors.algolab.client import (
    DEFAULT_USER_AGENT,
    AlgoLabClient,
    get_algolab_api_key,
)
from tradingagents.dataflows.vendors.ssi.client import (
    PRIMARY_TOKEN_FILE,
    SSIMCPClient,
    SSITokenManager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP Management"])

SSI_MCP_BASE = os.getenv("SSI_MCP_BASE", "https://mcp.ssi.com.vn")
SSI_REGISTER_ENDPOINT = f"{SSI_MCP_BASE}/oauth/register"
SSI_AUTHORIZE_ENDPOINT = f"{SSI_MCP_BASE}/oauth/authorize"
SSI_TOKEN_ENDPOINT = f"{SSI_MCP_BASE}/oauth/token"

# In-memory storage for pending OAuth state -> {verifier, client_id, redirect_uri, timestamp}
_pending_ssi_auth: dict[str, dict[str, Any]] = {}


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _generate_pkce() -> tuple[str, str, str]:
    verifier = _base64url_encode(secrets.token_bytes(32))
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = _base64url_encode(digest)
    state = secrets.token_hex(16)
    return verifier, challenge, state


def _register_ssi_client(redirect_uri: str) -> str:
    """Register an OAuth client via SSI Dynamic Client Registration (DCR)."""
    payload = {
        "client_name": "TradingAgents Web Console",
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    }
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Content-Type": "application/json",
    }
    res = httpx.post(SSI_REGISTER_ENDPOINT, json=payload, headers=headers, timeout=15.0)
    res.raise_for_status()
    data = res.json()
    return data["client_id"]


@router.get("/status", response_model=McpStatusResponse)
def get_mcp_status():
    """Return live status of configured MCP vendors (AlgoLab and SSI)."""
    # 1. Check AlgoLab
    algolab_key = get_algolab_api_key()
    algolab_status = AlgolabStatus(
        configured=bool(algolab_key),
        connected=False,
        api_key_masked=f"{algolab_key[:4]}...{algolab_key[-4:]}" if algolab_key and len(algolab_key) > 8 else (algolab_key[:4] + "..." if algolab_key else None),
        quota=None,
        error=None,
    )
    if algolab_key:
        try:
            client = AlgoLabClient.get_instance()
            # Probe tools/list or check cached quota
            res = client.call_rpc("tools/list", {})
            tools = res.get("result", {}).get("tools", [])
            algolab_status.connected = bool(tools)
            # Find any recent quota if present in client's last calls
        except Exception as exc:
            algolab_status.error = str(exc)

    # 2. Check SSI
    ssi_status = SsiStatus(
        configured=False,
        connected=False,
        client_id=None,
        expires_in=None,
        refreshed_at=None,
        token_file=None,
        error=None,
    )
    tm = SSITokenManager()
    auth_data = tm._read_cache()
    if auth_data:
        ssi_status.configured = True
        ssi_status.client_id = auth_data.get("client_id")
        tokens = auth_data.get("tokens", {})
        ssi_status.expires_in = tokens.get("expires_in")
        ssi_status.refreshed_at = auth_data.get("refreshed_at") or auth_data.get("created_at")
        ssi_status.token_file = str(tm._active_file) if tm._active_file else str(PRIMARY_TOKEN_FILE)

        # Quick connection test
        try:
            client = SSIMCPClient.get_instance()
            res = client.call_rpc("tools/list", {})
            tools = res.get("result", {}).get("tools", [])
            ssi_status.connected = bool(tools)
        except Exception as exc:
            ssi_status.error = str(exc)

    return McpStatusResponse(
        algolab=algolab_status,
        ssi=ssi_status,
        market="VN",
    )


@router.post("/ssi/auth/start", response_model=SsiAuthStartResponse)
def start_ssi_auth(req: SsiAuthStartRequest, request: Request):
    """Initiate SSI OAuth PKCE authorization flow."""
    # Determine callback redirect URI
    if req.redirect_uri:
        redirect_uri = req.redirect_uri
    else:
        base_url = str(request.base_url).rstrip("/")
        redirect_uri = f"{base_url}/api/mcp/ssi/callback"

    try:
        client_id = _register_ssi_client(redirect_uri)
    except Exception as exc:
        logger.warning("SSI DCR failed (%s); trying fallback client id", exc)
        # Try reading existing cached client_id
        tm = SSITokenManager()
        cached = tm._read_cache()
        if cached and cached.get("client_id"):
            client_id = cached["client_id"]
        else:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to register OAuth client with SSI MCP: {exc}",
            ) from exc

    verifier, challenge, state = _generate_pkce()

    # Clean old pending auths (> 10 mins)
    now = time.time()
    for s in list(_pending_ssi_auth.keys()):
        if now - _pending_ssi_auth[s].get("timestamp", 0) > 600:
            _pending_ssi_auth.pop(s, None)

    _pending_ssi_auth[state] = {
        "verifier": verifier,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "timestamp": now,
    }

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "market-data:read",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    auth_url = f"{SSI_AUTHORIZE_ENDPOINT}?{urlencode(params)}"

    return SsiAuthStartResponse(
        auth_url=auth_url,
        state=state,
        client_id=client_id,
    )


@router.get("/ssi/callback", response_class=HTMLResponse)
def ssi_oauth_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
):
    """Handle OAuth redirect callback from SSI authorization server."""
    if error:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head><title>SSI Authentication Failed</title>
            <style>
              body {{ font-family: system-ui, sans-serif; background: #09090b; color: #f43f5e; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
              .card {{ background: #18181b; border: 1px solid #27272a; padding: 2rem; border-radius: 12px; text-align: center; max-width: 440px; }}
              p {{ color: #a1a1aa; }}
            </style></head>
            <body><div class="card">
              <h2>Authentication Failed</h2>
              <p>SSI returned an error: <b>{error}</b></p>
              <p>Please close this window and try again.</p>
            </div></body></html>
            """,
            status_code=400,
        )

    if not code or not state:
        return HTMLResponse(
            content="<h3>Missing authorization code or state.</h3>",
            status_code=400,
        )

    pending = _pending_ssi_auth.pop(state, None)
    if not pending:
        return HTMLResponse(
            content="<h3>Invalid or expired authorization state session. Please initiate login again from TradingAgents.</h3>",
            status_code=400,
        )

    # Exchange authorization code for tokens
    payload = {
        "grant_type": "authorization_code",
        "client_id": pending["client_id"],
        "code": code,
        "redirect_uri": pending["redirect_uri"],
        "code_verifier": pending["verifier"],
    }
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    try:
        res = httpx.post(SSI_TOKEN_ENDPOINT, data=payload, headers=headers, timeout=15.0)
    except Exception as exc:
        return HTMLResponse(
            content=f"<h3>Failed to contact SSI token endpoint: {exc}</h3>",
            status_code=502,
        )

    if res.status_code != 200:
        return HTMLResponse(
            content=f"<h3>Token exchange rejected by SSI (HTTP {res.status_code}): {res.text}</h3>",
            status_code=400,
        )

    tokens = res.json()
    auth_data = {
        "client_id": pending["client_id"],
        "tokens": tokens,
        "created_at": time.time(),
        "refreshed_at": time.time(),
    }

    # Save to primary and fallback token cache files
    tm = SSITokenManager()
    tm._cached_auth = auth_data
    tm._write_cache(auth_data)

    # Invalidate singleton instances to pick up fresh tokens immediately
    SSIMCPClient._instance = None

    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
          <title>SSI MCP Authentication Success</title>
          <style>
            body { font-family: system-ui, -apple-system, sans-serif; background: #09090b; color: #f4f4f5; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .card { background: #18181b; border: 1px solid #27272a; padding: 2.5rem 2rem; border-radius: 14px; text-align: center; max-width: 420px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
            .icon { font-size: 40px; margin-bottom: 12px; }
            h2 { color: #10b981; margin: 0 0 10px 0; font-size: 20px; }
            p { color: #a1a1aa; font-size: 13.5px; line-height: 1.5; margin: 0 0 15px 0; }
            .hint { font-size: 11px; color: #71717a; }
          </style>
        </head>
        <body>
          <div class="card">
            <div class="icon">✅</div>
            <h2>SSI MCP Authenticated!</h2>
            <p>Your OAuth tokens have been verified and securely saved to your local TradingAgents credentials file.</p>
            <p class="hint">This window will close automatically in a moment...</p>
          </div>
          <script>
            try {
              if (window.opener) {
                window.opener.postMessage({ type: 'SSI_AUTH_SUCCESS' }, '*');
              }
            } catch (e) {}
            setTimeout(() => {
              window.close();
            }, 1800);
          </script>
        </body>
        </html>
        """
    )


@router.post("/ssi/tokens")
def submit_ssi_tokens(req: SsiTokensSubmitRequest):
    """Manually input or update SSI MCP tokens."""
    tokens = {
        "access_token": req.access_token.strip(),
        "token_type": "Bearer",
        "expires_in": 2592000,
    }
    if req.refresh_token:
        tokens["refresh_token"] = req.refresh_token.strip()

    auth_data = {
        "client_id": req.client_id.strip() if req.client_id else "custom",
        "tokens": tokens,
        "created_at": time.time(),
        "refreshed_at": time.time(),
    }

    tm = SSITokenManager()
    tm._cached_auth = auth_data
    tm._write_cache(auth_data)
    SSIMCPClient._instance = None

    return {"status": "ok", "message": "SSI tokens successfully stored"}


@router.post("/ssi/test", response_model=McpTestResponse)
def test_ssi_connection():
    """Verify live connectivity and tool availability on SSI MCP server."""
    tm = SSITokenManager()
    if not tm._read_cache():
        raise HTTPException(
            status_code=400,
            detail="SSI MCP is not configured. Please authenticate via OAuth or enter tokens.",
        )

    t0 = time.time()
    try:
        client = SSIMCPClient.get_instance()
        res = client.call_rpc("tools/list", {})
        latency = time.time() - t0
        tools = res.get("result", {}).get("tools", [])
        return McpTestResponse(
            status="ok",
            vendor="ssi",
            latency_ms=round(latency * 1000, 1),
            tools_count=len(tools),
            message=f"Connected successfully ({len(tools)} tools available)",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SSI MCP probe failed: {exc}") from exc


@router.post("/algolab/key")
def submit_algolab_key(req: AlgolabKeySubmitRequest):
    """Save ALGOLAB_API_KEY to environment and .env file."""
    key = req.api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="API key cannot be empty")

    os.environ["ALGOLAB_API_KEY"] = key

    # Persist into .env file
    env_path = Path(".env")
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("ALGOLAB_API_KEY="):
            new_lines.append(f"ALGOLAB_API_KEY={key}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"ALGOLAB_API_KEY={key}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Reset client singleton
    AlgoLabClient._instance = None

    # Probe key validity
    try:
        client = AlgoLabClient.get_instance()
        res = client.call_rpc("tools/list", {})
        tools = res.get("result", {}).get("tools", [])
        return {
            "status": "ok",
            "message": f"API key saved and verified ({len(tools)} tools active)",
            "tools_count": len(tools),
        }
    except Exception as exc:
        return {
            "status": "warning",
            "message": f"API key saved to .env, but connection test returned: {exc}",
        }


@router.post("/algolab/test", response_model=McpTestResponse)
def test_algolab_connection():
    """Verify live connectivity, tool listing, and quota on AlgoLab MCP server."""
    key = get_algolab_api_key()
    if not key:
        raise HTTPException(
            status_code=400,
            detail="ALGOLAB_API_KEY is not configured.",
        )

    t0 = time.time()
    try:
        client = AlgoLabClient.get_instance()
        res = client.call_rpc("tools/list", {})
        latency = time.time() - t0
        tools = res.get("result", {}).get("tools", [])

        # Try a fast probe to inspect meta quota
        probe_res = client.call_tool("get_company_profile", {"symbol": "VNM"}, use_cache=False)
        quota = None
        if isinstance(probe_res, dict) and "meta" in probe_res and "quota" in probe_res["meta"]:
            quota = probe_res["meta"]["quota"]

        return McpTestResponse(
            status="ok",
            vendor="algolab",
            latency_ms=round(latency * 1000, 1),
            tools_count=len(tools),
            quota=quota,
            message=f"Connected successfully ({len(tools)} tools available)",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AlgoLab MCP probe failed: {exc}") from exc
