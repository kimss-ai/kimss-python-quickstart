#!/usr/bin/env python3
"""Zero-rewrite adoption: official openai client + Kimss gateway + Agent-Id headers.

Env:
  KIMSS_API_KEY or KIMSS_WORKSPACE_KEY (required)
  KIMSS_AGENT_ID (required)
  KIMSS_MODEL (required)
  KIMSS_GATEWAY_URL or KIMSS_BASE_URL (optional)
  KIMSS_AGENT_NAME (optional)
"""
from __future__ import annotations

import os
import sys

from openai import OpenAI


def main() -> None:
    key = (os.environ.get("KIMSS_API_KEY") or os.environ.get("KIMSS_WORKSPACE_KEY") or "").strip()
    agent_id = (os.environ.get("KIMSS_AGENT_ID") or "").strip()
    model = (os.environ.get("KIMSS_MODEL") or "").strip()
    if not key or not agent_id or not model:
        print(
            "Set KIMSS_API_KEY (or KIMSS_WORKSPACE_KEY), KIMSS_AGENT_ID, and KIMSS_MODEL "
            "(see README steps 1-3).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    gateway = (os.environ.get("KIMSS_GATEWAY_URL") or "").strip()
    if not gateway:
        root = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
        gateway = f"{root}/v1" if not root.endswith("/v1") else root
    name = (os.environ.get("KIMSS_AGENT_NAME") or "Quickstart Agent").strip()

    client = OpenAI(base_url=gateway, api_key=key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "One sentence: why should AI traffic route through a gateway?",
            }
        ],
        extra_headers={
            "X-Kimss-Agent-Id": agent_id,
            "X-Kimss-Agent-Name": name,
        },
    )
    print(resp.choices[0].message.content)


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    main()
