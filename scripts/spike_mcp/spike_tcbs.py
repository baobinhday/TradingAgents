#!/usr/bin/env python3
"""
Throwaway Spike Client for TCBS MCP Server.
Probes TCBS endpoints, Cloudflare WAF behavior, OAuth discovery,
and test token access if provided.

Usage:
    uv run --with mcp python scripts/spike_mcp/spike_tcbs.py [--token <access_token>]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx

TCBS_MCP_URL = "https://mcp.tcbs.com.vn/mcp/tcinvest/"
TCBS_BASE = "https://mcp.tcbs.com.vn"
OUTPUT_DIR = Path(".trellis/tasks/11-02-vn-mcp-spike/research")


def probe_endpoints() -> dict[str, Any]:
    """Probe TCBS URLs with various HTTP methods and headers."""
    endpoints = [
        ("GET", TCBS_MCP_URL, {"Accept": "text/event-stream"}),
        ("POST", TCBS_MCP_URL, {"Content-Type": "application/json"}),
        ("GET", f"{TCBS_BASE}/.well-known/oauth-authorization-server", {}),
        ("GET", f"{TCBS_BASE}/.well-known/openid-configuration", {}),
        ("GET", f"{TCBS_BASE}/.well-known/oauth-protected-resource", {}),
        ("GET", f"{TCBS_MCP_URL}.well-known/oauth-protected-resource", {}),
    ]

    user_agents = [
        ("python-httpx", "python-httpx/0.28.1"),
        ("claude-desktop", "claude-desktop/1.0"),
        ("browser", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"),
    ]

    report: dict[str, Any] = {"probes": []}

    print("=" * 60)
    print("PROBING TCBS MCP NETWORK ENDPOINTS")
    print("=" * 60)

    with httpx.Client(follow_redirects=False, timeout=10.0) as client:
        for method, url, extra_headers in endpoints:
            for ua_name, ua_val in user_agents:
                headers = {"User-Agent": ua_val, **extra_headers}
                try:
                    t0 = time.time()
                    if method == "GET":
                        resp = client.get(url, headers=headers)
                    else:
                        resp = client.post(url, headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
                    latency = round(time.time() - t0, 3)

                    redirect_loc = resp.headers.get("location", "")
                    server = resp.headers.get("server", "")
                    cf_ray = resp.headers.get("cf-ray", "")

                    result_entry = {
                        "url": url,
                        "method": method,
                        "ua": ua_name,
                        "status_code": resp.status_code,
                        "redirect_location": redirect_loc,
                        "server": server,
                        "cf_ray": cf_ray,
                        "latency_s": latency,
                        "body_preview": resp.text[:200].replace("\n", " "),
                    }
                    report["probes"].append(result_entry)
                    print(f"[{method}] {url} (UA: {ua_name}) -> HTTP {resp.status_code} (Redirect: {redirect_loc or 'None'}) in {latency}s")
                except Exception as e:
                    print(f"[-] Error probing {url}: {e}")
                    report["probes"].append({"url": url, "method": method, "ua": ua_name, "error": str(e)})

    return report


async def probe_mcp_with_token(token: str) -> dict[str, Any]:
    """Test connecting to TCBS MCP using a Bearer token."""
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    results: dict[str, Any] = {}
    headers = {"Authorization": f"Bearer {token}"}
    print("\n[*] Connecting to TCBS MCP with token...")

    try:
        async with (
            sse_client(TCBS_MCP_URL, headers=headers, timeout=15.0) as (read, write),
            ClientSession(read, write) as session,
        ):
            init_res = await session.initialize()
            print(f"[+] TCBS MCP Connected! Server info: {init_res.serverInfo}")
            tools_res = await session.list_tools()
            results["tool_count"] = len(tools_res.tools)
            results["tools"] = [t.name for t in tools_res.tools]
            print(f"[+] Found {len(tools_res.tools)} tools on TCBS MCP.")
    except Exception as e:
        print(f"[-] TCBS MCP connection failed with token: {e}")
        results["error"] = str(e)

    return results


def main():
    parser = argparse.ArgumentParser(description="Spike TCBS MCP access")
    parser.add_argument("--token", type=str, default=None, help="Bearer token if extracted from TCInvest session")
    args = parser.parse_args()

    probe_data = probe_endpoints()

    if args.token:
        token_results = asyncio.run(probe_mcp_with_token(args.token))
        probe_data["token_probe"] = token_results

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "tcbs_probe_results.json"
    out_file.write_text(json.dumps(probe_data, indent=2, ensure_ascii=False))
    print(f"\n[+] TCBS probe results saved to {out_file}")


if __name__ == "__main__":
    main()
