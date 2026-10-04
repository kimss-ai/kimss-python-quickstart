# Getting started — first governed call

This repo is the 5-minute tutorial. Traffic is governed by the **Hermis** orchestration framework behind the Kimss Gateway. Full SDK docs: [kimss-ai/kimss-python-sdk](https://github.com/kimss-ai/kimss-python-sdk).

**Start with a 14-day Production trial (no card):** 100,000 governed requests/month during the trial. After the trial, core control-plane access continues until you subscribe.

1. Vault a provider key in **Governance → Provider Vault**.
2. Generate a `kimss_...` Gateway key.
3. Copy `.env.example` → `.env` and set `KIMSS_API_KEY`, `KIMSS_AGENT_ID`, `KIMSS_MODEL`.
4. Run `python example_02_openai_override.py` (OpenAI `base_url` swap) or `python example_01_gateway_proxy.py` (native SDK). Anthropic apps use the same Agent-Id headers with `ANTHROPIC_BASE_URL=https://api.kimss.ai` (the SDK appends `/v1/messages`).

Zero-code equivalent:

```bash
OPENAI_BASE_URL="https://api.kimss.ai/v1"
OPENAI_API_KEY="kimss_your_kimss_key"
# or
ANTHROPIC_BASE_URL="https://api.kimss.ai"
ANTHROPIC_API_KEY="kimss_your_kimss_key"
```

Kill switch refusals use HTTP 403 and code `agent_disabled`. See [example_03_kill_switch_and_429.py](example_03_kill_switch_and_429.py).
