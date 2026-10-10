#!/usr/bin/env python3
"""Zero-signup local demo: simulate the Kimss gateway contract on loopback.

Starts a tiny OpenAI-compatible HTTP server on 127.0.0.1:8787, then drives it
with the official ``openai`` SDK. No Kimss account, no provider key, no network
beyond localhost.

This is a **local simulator** of gateway behaviour — not the Kimss product and
not a real model call.

Env:
  KIMSS_DEMO_MODE=kill_switch  — return 403 agent_disabled
  KIMSS_DEMO_MODE=exhausted    — return 429 governed_requests_exhausted
"""
from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from openai import APIStatusError, OpenAI, PermissionDeniedError, RateLimitError

HOST = "127.0.0.1"
PORT = 8787
DEMO_KEY = "kimss_demo_key"
DEMO_AGENT_ID = "demo_agent"
DEMO_AGENT_NAME = "Quickstart Demo Agent"


def _year_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    payload = json.dumps(body).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


class LocalGatewayHandler(BaseHTTPRequestHandler):
    server_version = "KimssLocalDemo/0.1"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        if self.path not in ("/v1/chat/completions", "/chat/completions"):
            self.send_error(404, "Not Found")
            return

        auth = (self.headers.get("Authorization") or "").strip()
        if not auth.startswith("Bearer ") or auth[7:].strip() != DEMO_KEY:
            _json_response(
                self,
                401,
                {
                    "error": {
                        "message": "Invalid or missing API key.",
                        "type": "invalid_request_error",
                        "code": "invalid_api_key",
                    }
                },
            )
            return

        agent_id = (self.headers.get("X-Kimss-Agent-Id") or "").strip()
        if not agent_id:
            _json_response(
                self,
                400,
                {
                    "error": {
                        "message": "X-Kimss-Agent-Id header is required.",
                        "type": "invalid_request_error",
                        "code": "missing_agent_id",
                    }
                },
            )
            return

        agent_name = (self.headers.get("X-Kimss-Agent-Name") or DEMO_AGENT_NAME).strip()
        mode = (os.environ.get("KIMSS_DEMO_MODE") or "").strip().lower()

        if mode == "kill_switch":
            _json_response(
                self,
                403,
                {
                    "error": "agent_disabled",
                    "message": "This agent has been disabled by a workspace administrator.",
                    "agent_id": agent_id,
                },
            )
            return

        if mode == "exhausted":
            used, included = 25000, 25000
            _json_response(
                self,
                429,
                {
                    "error": "governed_requests_exhausted",
                    "message": (
                        f"Governed-request allowance reached ({used}/{included} this month). "
                        "Upgrade or wait until next month; audit events are not silently dropped."
                    ),
                    "used": used,
                    "included": included,
                    "year_month": _year_month(),
                },
            )
            return

        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            request_body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            request_body = {}

        model = str(request_body.get("model") or "demo-model")
        messages = request_body.get("messages") or []
        user_text = ""
        if messages and isinstance(messages[-1], dict):
            user_text = str(messages[-1].get("content") or "")

        completion_id = f"chatcmpl-demo-{uuid.uuid4().hex[:12]}"
        reply = (
            "This reply came from the local gateway simulator — no provider was called. "
            "In production, Kimss would forward this request to your vaulted OpenAI or "
            "Anthropic endpoint after identity, policy, and audit checks."
        )
        if user_text:
            reply = f"{reply} (You asked: {user_text[:120]})"

        audit_event = {
            "event": "governed_request",
            "agent_id": agent_id,
            "agent_name": agent_name,
            "model": model,
            "status": "routed",
            "simulated": True,
        }
        print(f"[gateway] audit: {json.dumps(audit_event)}")

        _json_response(
            self,
            200,
            {
                "id": completion_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": reply},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 28, "total_tokens": 40},
            },
        )


def _start_server() -> tuple[HTTPServer, threading.Thread]:
    class ReuseHTTPServer(HTTPServer):
        allow_reuse_address = True

    httpd = ReuseHTTPServer((HOST, PORT), LocalGatewayHandler)
    httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread


def _print_trace() -> None:
    lines = [
        "[ok] Request authenticated",
        "[ok] Agent identified",
        "[ok] Policy evaluated",
        "[ok] Request routed",
        "[ok] Audit event recorded",
    ]
    for line in lines:
        print(line)


def main() -> None:
    mode = (os.environ.get("KIMSS_DEMO_MODE") or "").strip().lower()
    if mode:
        print(f"Demo mode: {mode}")

    httpd, _thread = _start_server()
    base_url = f"http://{HOST}:{PORT}/v1"

    try:
        client = OpenAI(base_url=base_url, api_key=DEMO_KEY)
        resp = client.chat.completions.create(
            model="demo-model",
            messages=[
                {
                    "role": "user",
                    "content": "Why route AI traffic through a gateway?",
                }
            ],
            extra_headers={
                "X-Kimss-Agent-Id": DEMO_AGENT_ID,
                "X-Kimss-Agent-Name": DEMO_AGENT_NAME,
            },
        )
        print()
        _print_trace()
        print()
        print("--- assistant reply ---")
        print(resp.choices[0].message.content)
        print()
        print(
            "This was a local simulator only. To route real traffic through Kimss, "
            "follow the 3-step setup in README.md."
        )
    except (APIStatusError, PermissionDeniedError, RateLimitError) as exc:
        body = exc.response.json() if exc.response is not None else {}
        detail = body if isinstance(body, dict) else {}
        code = detail.get("error")
        if isinstance(code, dict):
            code = code.get("code") or code.get("message")
        status = getattr(exc, "status_code", None) or (
            exc.response.status_code if exc.response is not None else 0
        )
        if status == 403 and code == "agent_disabled":
            print(
                f"Agent {DEMO_AGENT_ID} is disabled by the kill switch. "
                "Re-enable it under Agents (/app/agents) in the Kimss dashboard."
            )
            raise SystemExit(3)
        if status == 429 and code == "governed_requests_exhausted":
            used = detail.get("used")
            included = detail.get("included")
            print(
                f"Monthly allowance reached ({used}/{included} governed requests). "
                "The meter resets next month; upgrade at https://kimss.ai/pricing "
                "for a larger allowance and longer telemetry retention."
            )
            raise SystemExit(2)
        print(f"Gateway refused the call ({status}): {detail or exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    main()
