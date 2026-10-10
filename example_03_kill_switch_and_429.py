#!/usr/bin/env python3
"""What enforcement looks like in code: typed errors instead of silent failures.

Two governance signals every integration should handle:

1. ``429 governed_requests_exhausted`` - the free tier hard cap
   (25,000 governed requests/month). Do not retry in a tight loop; the meter
   resets next month.
2. Kill-switch refusal - an operator disabled the agent under
   Agents (/app/agents); routed calls are refused until it is re-enabled.

Env: KIMSS_API_KEY (required), KIMSS_AGENT_ID (required), KIMSS_BASE_URL (optional).
"""
from __future__ import annotations

import os
import sys

from kimss import KimssApiError, KimssClient

try:  # kimss >= 2.1 exposes the typed governed-requests error
    from kimss import KimssGovernedRequestsExhausted
except ImportError:  # older SDK: fall back to error_code matching below
    KimssGovernedRequestsExhausted = None  # type: ignore[assignment]


def main() -> None:
    key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    agent_id = (os.environ.get("KIMSS_AGENT_ID") or "").strip()
    if not key or not agent_id:
        print("Set KIMSS_API_KEY and KIMSS_AGENT_ID in .env.", file=sys.stderr)
        raise SystemExit(1)
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    client = KimssClient(api_key=key, base_url=base)

    try:
        result = client.agents.run(agent_id, "Governed call with error handling.", stream=False)
        print("OK:", result.text)
        return
    except KimssApiError as exc:
        code = (exc.error_code or "").strip()
        if KimssGovernedRequestsExhausted is not None and isinstance(
            exc, KimssGovernedRequestsExhausted
        ):
            code = "governed_requests_exhausted"
        if code == "governed_requests_exhausted":
            used = exc.detail.get("used")
            included = exc.detail.get("included")
            print(
                f"Monthly allowance reached ({used}/{included} governed requests). "
                "The meter resets next month; upgrade at https://kimss.ai/pricing "
                "for a larger allowance and longer telemetry retention."
            )
            raise SystemExit(2)
        if code in ("agent_disabled", "agent_killed"):
            print(
                f"Agent {agent_id} is disabled by the kill switch. "
                "Re-enable it under Agents (/app/agents) in the Kimss dashboard."
            )
            raise SystemExit(3)
        print(f"Gateway refused the call ({exc.status_code} {code or 'error'}): {exc}")
        raise SystemExit(4)


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    main()
