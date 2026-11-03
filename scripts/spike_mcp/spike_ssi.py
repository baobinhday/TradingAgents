#!/usr/bin/env python3
"""
Throwaway Spike Client for SSI MCP Server.
Tests OAuth DCR, PKCE, Token Exchange, Token Refresh, Streamable HTTP POST MCP transport,
Tool listing & schemas, Resource catalogs, and Vietnam market data probes.

Usage:
    uv run python scripts/spike_mcp/spike_ssi.py [--skip-auth]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import httpx

SSI_MCP_BASE = "https://mcp.ssi.com.vn"
SSI_REGISTER_ENDPOINT = f"{SSI_MCP_BASE}/oauth/register"
SSI_AUTHORIZE_ENDPOINT = f"{SSI_MCP_BASE}/oauth/authorize"
SSI_TOKEN_ENDPOINT = f"{SSI_MCP_BASE}/oauth/token"
SSI_MCP_SERVER_URL = f"{SSI_MCP_BASE}/mcp"

OUTPUT_DIR = Path(".trellis/tasks/11-02-vn-mcp-spike/research")
CACHE_FILE = Path("scripts/spike_mcp/.ssi_auth_cache.json")


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def generate_pkce() -> tuple[str, str, str]:
    verifier = base64url_encode(secrets.token_bytes(32))
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64url_encode(digest)
    state = secrets.token_hex(16)
    return verifier, challenge, state


def register_client(redirect_uri: str) -> str:
    payload = {
        "client_name": "TradingAgents Spike",
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    }
    print(f"[*] Registering OAuth client at {SSI_REGISTER_ENDPOINT}...")
    res = httpx.post(SSI_REGISTER_ENDPOINT, json=payload, timeout=15.0)
    res.raise_for_status()
    data = res.json()
    client_id = data["client_id"]
    print(f"[+] Client registered successfully! client_id={client_id}")
    return client_id


class CallbackHandler(BaseHTTPRequestHandler):
    captured_code: str | None = None
    captured_state: str | None = None
    captured_error: str | None = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/callback":
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                CallbackHandler.captured_code = params["code"][0]
                CallbackHandler.captured_state = params.get("state", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"""
                <html>
                <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                    <h2 style="color: #10b981;">Authentication Successful!</h2>
                    <p>Authorization code received. You can now close this browser tab.</p>
                </body>
                </html>
                """)
            else:
                error = params.get("error", ["unknown"])[0]
                CallbackHandler.captured_error = error
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h2>Authentication failed: {error}</h2>".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def run_oauth_flow(client_id: str, port: int) -> tuple[dict[str, Any], str]:
    redirect_uri = f"http://localhost:{port}/callback"
    verifier, challenge, state = generate_pkce()

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "market-data:read",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    auth_url = f"{SSI_AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}"

    server = HTTPServer(("0.0.0.0", port), CallbackHandler)
    server.timeout = 1.0

    print("\n" + "=" * 70)
    print("ACTION REQUIRED: Log into SSI to authorize connection")
    print("=" * 70)
    print(f"\n  {auth_url}\n")
    print(f"Waiting for callback on {redirect_uri} ...\n", flush=True)

    code = None
    start_time = time.time()
    while time.time() - start_time < 300:
        server.handle_request()
        if CallbackHandler.captured_code:
            code = CallbackHandler.captured_code
            break
        if CallbackHandler.captured_error:
            print(f"[-] Authorization returned error: {CallbackHandler.captured_error}")
            sys.exit(1)

    server.server_close()

    if not code:
        print("[-] Timed out waiting for callback.")
        try:
            manual_input = input("Paste the authorization code (or full redirect URL): ").strip()
            if "code=" in manual_input:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(manual_input).query)
                code = qs["code"][0]
            else:
                code = manual_input
        except (EOFError, KeyboardInterrupt):
            pass

    if not code:
        print("[-] No code received.")
        sys.exit(1)

    print(f"[+] Received authorization code: {code[:8]}... (length={len(code)})")
    token_data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    }
    res = httpx.post(SSI_TOKEN_ENDPOINT, data=token_data, timeout=15.0)
    res.raise_for_status()
    tokens = res.json()
    return tokens, verifier


def test_token_refresh(client_id: str, refresh_token: str) -> dict[str, Any] | None:
    print("\n[*] Testing token refresh with refresh_token...")
    refresh_data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }
    t_start = time.time()
    res = httpx.post(SSI_TOKEN_ENDPOINT, data=refresh_data, timeout=15.0)
    t_latency = time.time() - t_start
    if res.status_code == 200:
        new_tokens = res.json()
        print(f"[+] Refresh SUCCESS in {t_latency:.2f}s! expires_in={new_tokens.get('expires_in')}s")
        print("[+] SSI uses single-use Refresh Token Rotation (RFC 6749 Section 6).")
        # Update cache with rotated tokens
        if CACHE_FILE.exists():
            try:
                cache = json.loads(CACHE_FILE.read_text())
                cache["tokens"] = new_tokens
                cache["refreshed_at"] = time.time()
                CACHE_FILE.write_text(json.dumps(cache, indent=2))
                print("[+] Updated auth cache with rotated tokens.")
            except Exception:
                pass
        return new_tokens
    else:
        print(f"[!] Token refresh returned HTTP {res.status_code}: {res.text}")
        print("[!] Note: SSI enforces Refresh Token Rotation; if a refresh token was already used once, it becomes invalid_grant.")
        return None


class SSIMCPClient:
    """Streamable HTTP POST transport client for SSI MCP."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        self.client = httpx.Client(timeout=35.0)
        self.req_id = 0

    def call_rpc(self, method: str, params: dict | None = None) -> dict[str, Any]:
        self.req_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": method,
            "params": params or {},
        }
        t0 = time.time()
        res = self.client.post(SSI_MCP_SERVER_URL, json=payload, headers=self.headers)
        latency = time.time() - t0
        res.raise_for_status()

        # Parse SSE lines: find data: {...}
        for line in res.text.split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                data_obj = json.loads(line[6:])
                data_obj["_latency_s"] = round(latency, 3)
                data_obj["_http_status"] = res.status_code
                return data_obj

        raise ValueError(f"No SSE data line in response: {res.text[:200]}")

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        rpc_res = self.call_rpc("tools/call", {"name": name, "arguments": arguments})
        result = rpc_res.get("result", {})
        latency = rpc_res.get("_latency_s", 0)

        # Unpack inner JSON content if present
        content = result.get("content", [])
        parsed_data = None
        if content and isinstance(content, list) and "text" in content[0]:
            try:
                parsed_data = json.loads(content[0]["text"])
            except Exception:
                parsed_data = content[0]["text"]

        return {
            "tool": name,
            "arguments": arguments,
            "latency_s": latency,
            "isError": result.get("isError", False),
            "data": parsed_data,
        }


def run_probes(mcp: SSIMCPClient) -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tools": {},
        "resources": {},
        "probes": {},
    }

    # 1. Initialize
    print("[*] Initializing MCP session...")
    init_res = mcp.call_rpc("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "tradingagents-spike", "version": "1.0"},
    })
    server_info = init_res.get("result", {}).get("serverInfo", {})
    report["server_info"] = server_info
    print(f"[+] Initialized: {server_info}")

    # 2. Tools list
    print("\n[*] Fetching tools/list...")
    tools_res = mcp.call_rpc("tools/list")
    tools = tools_res.get("result", {}).get("tools", [])
    report["tools"]["count"] = len(tools)
    report["tools"]["names"] = [t["name"] for t in tools]
    schema_file = OUTPUT_DIR / "ssi_tools_schema.json"
    schema_file.write_text(json.dumps(tools, indent=2, ensure_ascii=False))
    print(f"[+] Found {len(tools)} tools. Saved schemas to {schema_file}")

    # 3. Resources list
    print("\n[*] Fetching resources/list...")
    res_res = mcp.call_rpc("resources/list")
    resources = res_res.get("result", {}).get("resources", [])
    report["resources"]["count"] = len(resources)
    report["resources"]["items"] = resources
    res_file = OUTPUT_DIR / "ssi_resources.json"
    res_file.write_text(json.dumps(resources, indent=2, ensure_ascii=False))
    print(f"[+] Found {len(resources)} resources. Saved to {res_file}")

    # Read reference resources
    resource_contents = {}
    for r in resources:
        uri = r["uri"]
        try:
            print(f"[*] Reading resource: {uri}...")
            r_read = mcp.call_rpc("resources/read", {"uri": uri})
            contents = r_read.get("result", {}).get("contents", [])
            resource_contents[uri] = contents
        except Exception as e:
            print(f"[-] Could not read resource {uri}: {e}")
    (OUTPUT_DIR / "ssi_resource_contents.json").write_text(json.dumps(resource_contents, indent=2, ensure_ascii=False))

    # 4. Req 4 & 9: Market data across HOSE, HNX, UPCoM + Sectors
    print("\n" + "=" * 60)
    print("PROBING DAILY STOCK DATA (Req 4, 8, 9)")
    print("=" * 60)
    sample_symbols = [
        ("SSI", "HOSE", "Securities"),
        ("VCB", "HOSE", "Bank"),
        ("BVH", "HOSE", "Insurance"),
        ("PVS", "HNX", "Oil/Gas"),
        ("BSR", "UPCOM", "Refinery"),
    ]

    daily_data_probes = {}
    for sym, exch, sector in sample_symbols:
        print(f"[*] Calling marketdata_list_stock_daily_data for {sym} ({exch}, {sector}, range=3m)...")
        res = mcp.call_tool("marketdata_list_stock_daily_data", {"symbol": sym, "range": "3m"})
        daily_data_probes[sym] = {
            "exchange": exch,
            "sector": sector,
            "latency_s": res["latency_s"],
            "isError": res["isError"],
            "data": res["data"],
        }
        status = res["data"].get("status") if isinstance(res["data"], dict) else "raw"
        count = len(res["data"].get("data", {}).get("stocks", [])) if isinstance(res["data"], dict) and isinstance(res["data"].get("data"), dict) else 0
        print(f"    -> Status: {status}, Records: {count}, Latency: {res['latency_s']}s")
        time.sleep(0.4)

    report["probes"]["marketdata_list_stock_daily_data"] = daily_data_probes

    # Probe marketdata_list_daily_stock_infor for VNM (detailed infor with foreign flow)
    print("\n[*] Calling marketdata_list_daily_stock_infor for VNM (detailed infor)...")
    res_infor = mcp.call_tool("marketdata_list_daily_stock_infor", {"symbol": "VNM", "range": "3m"})
    report["probes"]["marketdata_list_daily_stock_infor"] = res_infor
    print(f"    -> Latency: {res_infor['latency_s']}s, isError: {res_infor['isError']}")
    time.sleep(0.4)

    # 5. Req 6: News window limit (>6 months vs <=6 months)
    print("\n" + "=" * 60)
    print("PROBING NEWS WINDOW LIMITS (Req 6)")
    print("=" * 60)
    news_probes = {}
    for rng in ["1m", "3m", "6m", "1y", "max_range"]:
        print(f"[*] Calling marketdata_list_company_news for SSI with range={rng}...")
        res = mcp.call_tool("marketdata_list_company_news", {"symbol": "SSI", "range": rng})
        news_probes[rng] = res
        err_msg = ""
        if res["isError"] and isinstance(res["data"], dict):
            err_msg = res["data"].get("error", {}).get("message", "")
        print(f"    -> range={rng}: isError={res['isError']} {err_msg}")
        time.sleep(0.4)
    report["probes"]["news_windows"] = news_probes

    # 6. Req 7: Financial Statements & Indicators
    print("\n" + "=" * 60)
    print("PROBING FINANCIAL STATEMENTS (Req 7)")
    print("=" * 60)
    fin_probes = {}
    for tool_name, args in [
        ("marketdata_list_financial_statement", {"symbol": "SSI", "yearReport": "2025", "lengthReport": "4"}),
        ("marketdata_list_financial_statement", {"symbol": "VCB", "yearReport": "2025", "lengthReport": "4"}),
        ("marketdata_list_finance_indicator", {"symbol": "SSI", "range": "1y"}),
        ("fundamental_get_financial_statement", {"symbol": "SSI", "range": "1y"}),
        ("fundamental_get_key_metrics", {"symbol": "SSI"}),
    ]:
        if tool_name in report["tools"]["names"]:
            print(f"[*] Calling {tool_name} with {args}...")
            res = mcp.call_tool(tool_name, args)
            fin_probes[f"{tool_name}_{args.get('symbol')}"] = res
            print(f"    -> Latency: {res['latency_s']}s, isError: {res['isError']}")
            time.sleep(0.4)
    report["probes"]["financials"] = fin_probes

    # 7. Index Data (VNINDEX / VN30)
    print("\n" + "=" * 60)
    print("PROBING INDEX DATA (VNINDEX, VN30)")
    print("=" * 60)
    index_probes = {}
    for idx_code in ["VNINDEX", "VN30"]:
        print(f"[*] Calling marketdata_list_index_daily_data for {idx_code}...")
        res = mcp.call_tool("marketdata_list_index_daily_data", {"indexCode": idx_code, "range": "3m"})
        index_probes[idx_code] = res
        print(f"    -> Latency: {res['latency_s']}s, isError: {res['isError']}")
        time.sleep(0.4)
    report["probes"]["index_data"] = index_probes

    return report


def main():
    parser = argparse.ArgumentParser(description="Spike SSI MCP server")
    parser.add_argument("--port", type=int, default=8080, help="Local callback port")
    parser.add_argument("--client-id", type=str, default=None, help="Existing client_id")
    parser.add_argument("--skip-auth", action="store_true", help="Use cached tokens if present")
    args = parser.parse_args()

    client_id = args.client_id
    tokens = None

    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text())
            tokens = cache.get("tokens")
            client_id = cache.get("client_id")
            print(f"[+] Loaded cached auth for client_id={client_id}")
        except Exception:
            pass

    if not tokens:
        redirect_uri = f"http://localhost:{args.port}/callback"
        if not client_id:
            client_id = register_client(redirect_uri)

        tokens, verifier = run_oauth_flow(client_id, args.port)
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({
            "client_id": client_id,
            "tokens": tokens,
            "created_at": time.time(),
        }, indent=2))
        print(f"[+] Cached tokens to {CACHE_FILE}")

    # Inspect token details
    print("\n" + "=" * 50)
    print("TOKEN OBSERVATIONS (Req 1, 2)")
    print("=" * 50)
    print(f"Access Token: {tokens['access_token'][:10]}... (len={len(tokens['access_token'])})")
    print(f"Token Type: {tokens.get('token_type')}")
    print(f"Expires In: {tokens.get('expires_in')} seconds (~{tokens.get('expires_in', 0)/3600:.1f} hours / {tokens.get('expires_in', 0)/86400:.1f} days)")
    refresh_token = tokens.get("refresh_token")
    print(f"Refresh Token Present: {bool(refresh_token)}")

    if refresh_token:
        # Test token refresh
        test_token_refresh(client_id, refresh_token)

    # Run Streamable HTTP POST Probes
    print("\n" + "=" * 50)
    print("RUNNING STREAMABLE HTTP POST PROBES")
    print("=" * 50)
    mcp = SSIMCPClient(tokens["access_token"])
    report = run_probes(mcp)

    out_file = OUTPUT_DIR / "ssi_probe_results.json"
    out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n[+] Full SSI probe results saved to {out_file}")
    print("[+] SSI Spike Complete!")


if __name__ == "__main__":
    main()
