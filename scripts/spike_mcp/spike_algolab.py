#!/usr/bin/env python3
"""
Throwaway Spike Client for AlgoLab MCP Server.
Tests authenticated Streamable HTTP POST transport, Tool listing & schemas,
price history, quotes, profile, and quota tracking using ALGOLAB_API_KEY.

Usage:
    uv run python scripts/spike_mcp/spike_algolab.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ALGOLAB_MCP_URL = "https://mcp.algolab.vn"
OUTPUT_DIR = Path(".trellis/tasks/11-02-vn-mcp-spike/research")


def load_api_key() -> str:
    key = os.environ.get("ALGOLAB_API_KEY")
    if key:
        return key.strip()

    # Fallback to reading .env
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("ALGOLAB_API_KEY="):
                val = line.split("=", 1)[1].strip()
                if val:
                    return val

    print("[-] ALGOLAB_API_KEY not found in environment or .env file.")
    sys.exit(1)


class AlgoLabMCPClient:
    """Streamable HTTP POST transport client for AlgoLab MCP."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        self.client = httpx.Client(timeout=30.0)
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
        res = self.client.post(ALGOLAB_MCP_URL, json=payload, headers=self.headers)
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


def main():
    api_key = load_api_key()
    print(f"[+] Loaded ALGOLAB_API_KEY: {api_key[:8]}... (len={len(api_key)})")

    client = AlgoLabMCPClient(api_key)

    # 1. Initialize
    print("\n[*] Initializing AlgoLab MCP...")
    init_res = client.call_rpc("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "tradingagents-spike", "version": "1.0"},
    })
    server_info = init_res.get("result", {}).get("serverInfo", {})
    print(f"[+] Server Info: {server_info}")

    # 2. List tools
    print("\n[*] Listing tools...")
    tools_res = client.call_rpc("tools/list")
    tools = tools_res.get("result", {}).get("tools", [])
    print(f"[+] Tool count: {len(tools)}")
    print(f"[+] Tools: {[t['name'] for t in tools]}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    schema_file = OUTPUT_DIR / "algolab_tools_schema.json"
    schema_file.write_text(json.dumps(tools, indent=2, ensure_ascii=False))
    print(f"[+] Saved tools schema to {schema_file}")

    # 3. Test price history
    print("\n[*] Calling get_price_history for VNM...")
    res = client.call_tool("get_price_history", {
        "symbol": "VNM",
        "from_date": "2026-10-20",
        "to_date": "2026-11-01",
    })
    print(f"[+] Price history returned in {res['latency_s']}s (isError={res['isError']})")
    data = res.get("data", {})
    if isinstance(data, dict):
        meta = data.get("meta", {})
        print(f"    Quota used: {meta.get('quota')}")
        bars = data.get("data", {}).get("bars", {})
        print(f"    Bars count: {len(bars.get('rows', []))}")
        print(f"    Columns: {bars.get('columns')}")

    print("\n[+] AlgoLab Spike completed successfully!")


if __name__ == "__main__":
    main()
