"""Client for AIsa, the radar's one paid dependency: its tool router (X posts, Google
Trends and whois data through DataForSEO) and its OpenAI-compatible chat endpoint (the
name judge). Key: credentials.aisa_api_key in the loaded local JSON file.

The tool router runs a batch's calls one by one, about 10 s each, so batches are kept to
BATCH calls and the timeout is long. Every call is billed: a failed batch is never
retried here, so one bad day costs one batch at most.

Prices seen in October 2026: an account's last 20 posts $0.003, one Trends task $0.0012,
one whois overview query about $0.13.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from . import UA, settings

ROUTER = "https://tools.aisa.one/v1/tool-router/aisa-batch-use"
CHAT = "https://api.aisa.one/v1/chat/completions"
MAX_CALLS = 20      # the router's own limit per batch
BATCH = 5           # what call_all sends at once, about 50 s a batch
TIMEOUT = 240
CHAT_TIMEOUT = 90


class AisaError(RuntimeError):
    pass


def key() -> str:
    """Only credentials.aisa_api_key from the loaded config file."""
    k = settings.credential("aisa_api_key")
    if k:
        return k
    return _no_key()


def _no_key() -> str:
    raise AisaError("no AIsa key: fill credentials.aisa_api_key in the local config file")


def _post(url: str, body: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key()}",
        "User-Agent": UA, "x-aisa-source": "new-term-radar"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.load(res)
    except urllib.error.HTTPError as exc:
        raise AisaError(f"HTTP {exc.code}: {' '.join(exc.read().decode('utf-8', 'replace').split())[:200]}") from exc
    except (OSError, ValueError) as exc:
        raise AisaError(f"{type(exc).__name__}: {exc}") from exc


def call(calls: list[dict]) -> tuple[dict[str, dict], int]:
    """Run one batch of tool calls. Returns ({call_id: data}, cost in micro-USD). Calls
    that failed are left out of the dict; only a failed request raises."""
    if not calls:
        return {}, 0
    if len(calls) > MAX_CALLS:
        raise AisaError(f"{len(calls)} calls in one batch, the cap is {MAX_CALLS}")
    url = settings.service("aisa_router_base_url", "https://tools.aisa.one") + "/v1/tool-router/aisa-batch-use"
    body = _post(url, {"calls": calls}, TIMEOUT)
    if "error" in body:
        raise AisaError(str(body["error"].get("message") or body["error"])[:200])
    out, cost = {}, 0
    for r in body.get("results", []):
        cost += int(r.get("customer_cost_micros_usd") or 0)
        if r.get("successful"):
            out[r["call_id"]] = r.get("data") or {}
    return out, cost


def call_all(calls: list[dict]) -> tuple[dict[str, dict], int]:
    """call() in batches of BATCH. A failed batch raises and stops the rest."""
    out, cost = {}, 0
    for i in range(0, len(calls), BATCH):
        data, c = call(calls[i:i + BATCH])
        out.update(data)
        cost += c
    return out, cost


def chat(model: str, system: str, user: str, max_tokens: int = 1500) -> str:
    url = settings.service("aisa_api_base_url", "https://api.aisa.one") + "/v1/chat/completions"
    body = _post(url, {"model": model, "temperature": 0, "max_tokens": max_tokens, "messages": [
        {"role": "system", "content": system}, {"role": "user", "content": user}]}, CHAT_TIMEOUT)
    try:
        return body["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise AisaError(f"unexpected chat answer: {str(body)[:160]}") from exc
