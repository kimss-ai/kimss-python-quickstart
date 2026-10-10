# AI gateway quickstart for Python — OpenAI & Anthropic compatible

[![PyPI](https://img.shields.io/pypi/v/kimss.svg?color=indigo)](https://pypi.org/project/kimss/)
[![Python](https://img.shields.io/pypi/pyversions/kimss.svg?color=purple)](https://pypi.org/project/kimss/)
[![License: MIT](https://img.shields.io/badge/License-MIT-indigo.svg)](LICENSE)
[![CI](https://github.com/kimss-ai/kimss-python-quickstart/actions/workflows/ci.yml/badge.svg)](https://github.com/kimss-ai/kimss-python-quickstart/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/kimss-ai/kimss-python-quickstart/badge)](https://scorecard.dev/viewer/?uri=github.com/kimss-ai/kimss-python-quickstart)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/14215/badge)](https://www.bestpractices.dev/projects/14215)

**Track, govern, and secure autonomous agents with exactly 1 line of code. Zero data-plane refactoring required.**

Put an enforcement and observability layer between your Python application and OpenAI or Anthropic — identity, audit logging, spend limits, and kill switches — without rewriting your app.

## Before → After

**Before** — call the provider directly:

```python
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)
```

**After** — route through an AI gateway (one-line change):

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.kimss.ai/v1",
    api_key=KIMSS_API_KEY,
)
```

Your application keeps using the native OpenAI SDK. No model migration. No application rewrite. The gateway becomes the control point.

<p align="center">
  <img src="docs/invisible-proxy-architecture.svg" alt="Invisible proxy pattern: your native OpenAI or Anthropic SDK talks to the Kimss Gateway. Identity, policy, audit, spend limits, and a kill switch sit between your app and your vaulted provider." width="100%">
</p>

<p align="center"><em>Invisible proxy — keep your native SDK. The gateway governs every hop.</em></p>

---

## Try it now — no account required

Clone and run a **local gateway simulator** (no Kimss signup, no provider key, no network beyond localhost):

```bash
git clone https://github.com/kimss-ai/kimss-python-quickstart.git
cd kimss-python-quickstart
pip install -r requirements.txt
python demo_local_gateway.py
```

Expected output:

```text
[ok] Request authenticated
[ok] Agent identified
[ok] Policy evaluated
[ok] Request routed
[ok] Audit event recorded

--- assistant reply ---
This reply came from the local gateway simulator — no provider was called.
```

> **Note:** `demo_local_gateway.py` simulates the gateway contract on loopback. It is not Kimss itself and does not call any model provider. Use the 3-step setup below to route real traffic.

Try enforcement modes:

```bash
KIMSS_DEMO_MODE=kill_switch python demo_local_gateway.py   # 403 agent_disabled
KIMSS_DEMO_MODE=exhausted python demo_local_gateway.py     # 429 governed_requests_exhausted
```

---

## Why this exists

AI agents increasingly have access to production APIs, databases, and internal tools. The model is only one part of the system.

This quickstart demonstrates how to insert an **enforcement and observability layer** between your application and the model provider — without rewriting the application. [Kimss](https://kimss.ai) provides the gateway implementation; this repo shows the integration pattern.

---

## Start here

### 1. OpenAI SDK — zero-refactor gateway (recommended)

[`example_02_openai_override.py`](example_02_openai_override.py) — point the official `openai` client at the gateway with `base_url` + Agent-Id headers.

```bash
python example_02_openai_override.py
```

### Then explore

| # | Script | What it proves |
|---|--------|----------------|
| 2 | [`example_01_gateway_proxy.py`](example_01_gateway_proxy.py) | Raw HTTP / Kimss SDK path |
| 3 | [`example_03_kill_switch_and_429.py`](example_03_kill_switch_and_429.py) | Kill switch + monthly cap errors |

---

## 3-step setup (real gateway)

### 1. Sign In & Vault

[Create Free Account →](https://kimss.ai/app/signup). Open **Governance → Connected Infrastructure** and vault your provider endpoint + key.

### 2. Mint Key

**Gateway → Generate Key**. Copy `kimss_...`. Note your `agent_id` (or register one under Gateway).

### 3. Route Traffic (zero refactoring)

```bash
git clone https://github.com/kimss-ai/kimss-python-quickstart.git
cd kimss-python-quickstart
pip install -r requirements.txt
cp .env.example .env   # KIMSS_WORKSPACE_KEY / KIMSS_API_KEY, KIMSS_AGENT_ID, KIMSS_MODEL
python example_02_openai_override.py
```

Open **Gateway → Recent calls** to see the governed audit trail.

Dual-listener: OpenAI (`/v1/chat/completions`) and Anthropic (`/v1/messages`). Keep your native SDK.

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("KIMSS_GATEWAY_URL", "https://api.kimss.ai/v1"),
    api_key=os.getenv("KIMSS_WORKSPACE_KEY") or os.getenv("KIMSS_API_KEY"),
)
resp = client.chat.completions.create(
    model=os.getenv("KIMSS_MODEL", "custom:your-vaulted-model"),
    messages=[{"role": "user", "content": "Hello via Kimss"}],
    extra_headers={
        "X-Kimss-Agent-Id": os.getenv("KIMSS_AGENT_ID", "my_agent"),
        "X-Kimss-Agent-Name": os.getenv("KIMSS_AGENT_NAME", "My Agent"),
    },
)
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `401` / invalid API key | Wrong or missing `KIMSS_WORKSPACE_KEY` | Mint a new key under **Gateway → Generate Key** |
| `400` / missing agent | No `X-Kimss-Agent-Id` header | Set `KIMSS_AGENT_ID` and pass it via `extra_headers` |
| `403` / `agent_disabled` | Kill switch is on | **Re-enable** the agent under **Agents** (`/app/agents`) |
| `429` / `governed_requests_exhausted` | Monthly allowance reached | Wait for reset or upgrade at [kimss.ai/pricing](https://kimss.ai/pricing) |
| Model not found | Model not vaulted | Vault the provider endpoint + model under **Governance → Connected Infrastructure** |

---

## Related

- SDK: [kimss-ai/kimss-python-sdk](https://github.com/kimss-ai/kimss-python-sdk) · Control-plane spec: [kimss-ai/kimss-control-plane](https://github.com/kimss-ai/kimss-control-plane) · [kimss.ai](https://kimss.ai)
- Architecture: [Zero-Trust AI](https://kimss.ai/trust)
- AI coding assistants: canonical [control-plane `AI_INTEGRATION.md`](https://github.com/kimss-ai/kimss-control-plane/blob/main/AI_INTEGRATION.md) · local [AI_INTEGRATION.md](AI_INTEGRATION.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md) · Security: [SECURITY.md](SECURITY.md)

## License

MIT — see [LICENSE](LICENSE).
