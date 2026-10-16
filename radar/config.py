"""config.json: what to watch. Copy config.example.json and edit it.

Everything has a default except the X accounts and the sitemaps, which only you can
choose. Credentials and service addresses come only from this local JSON file.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import i18n, settings, terms

DEFAULTS = {
    "lang": "en",
    "x_accounts": {"labs": [], "bloggers": []},
    "sitemaps": {},
    "topics": {},
    "known_terms": [],
    "stop_words": [],
    "judge": {"model": "gpt-4.1-mini", "min_score": 0.5},
    "breakout": {"window_days": 14, "min_stars": 300, "velocity_min": 200, "delta_min": 400},
    "new_sites": {"queries": {"ai": "%ai%"}, "weekday": 0, "window_days": 90, "min_etv": 1000, "min_keywords": 20},
    "review": {"after_days": 14, "per_day": 5},
    "usecases": {"per_day": 5, "model": "claude-sonnet-4-6", "min_volume": 50, "trends_max": 10, "recheck_days": 3,
                 "location_code": 2840, "benchmark": "gpts", "min_daily": 300, "related": True, "related_geo": "US",
                 "country_trends": True, "country_min_volume": 1000, "country_max": 8},
    "competition": {"max_rows": 8, "weak_dr": 30, "location_code": 2840},
    "revenue": {"weekday": 0, "pages_growth": 3, "pages_new": 3, "min_revenue_usd": 500, "category": "", "max_leads": 10},
    "asks": {"weekday": 0, "time": "week", "min_score": 2, "model": "gpt-4.1-mini", "min_volume": 50, "max_leads": 12,
             "location_code": 2840, "patterns": [
                 '"is there an ai tool"', '"is there an ai that"', '"is there a tool that"', '"any ai tool for"',
                 '"looking for an ai tool"', '"i wish there was a tool"', '"is there a way to automatically"',
                 '"how do i automate"', '"tool that can automatically"', '"recommend an ai"', '"best ai tool for"',
                 '"ai tool that can"']},
    "pains": {"model": "gpt-4.1-mini", "extensions": 5, "review_pages": 2, "max_stars": 3, "reddit_time": "year", "videos": 3,
              "reddit_queries": ["{k} alternative", "{k} frustrating", '"{k}" "doesn\'t work"', "{k} wish there was"]},
    "tutorials": {"max_leads": 3, "videos": 3, "model": "gpt-4.1-mini"},
    "gsc": {},
    "credentials": {"aisa_api_key": "", "goanyapi_api_key": "", "github_token": "", "trustmrr_api_key": "",
                    "resend_api_key": "", "email_from": "", "email_to": []},
    "services": {"aisa_router_base_url": "https://tools.aisa.one", "aisa_api_base_url": "https://api.aisa.one",
                 "goanyapi_base_url": "https://api.goanyapi.com"},
}


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"{path} not found: copy config.example.json to {path.name} and edit it")
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError("config must be a JSON object")
    for group in ("credentials", "services"):
        values = raw.get(group, {})
        if not isinstance(values, dict):
            raise ValueError(f"{group} must be an object")
        unknown = values.keys() - DEFAULTS[group].keys()
        if unknown:
            raise ValueError(f"unknown {group} field(s): {', '.join(sorted(unknown))}")
        for name, value in values.items():
            valid = isinstance(value, str)
            if group == "credentials" and name == "email_to":
                valid = valid or (isinstance(value, list) and all(isinstance(x, str) for x in value))
            if not valid:
                raise ValueError(f"{group}.{name} has an invalid type")
            if group == "services":
                from urllib.parse import urlsplit
                parsed = urlsplit(value)
                if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
                    raise ValueError(f"services.{name} must be an HTTPS base URL without credentials/query/fragment")
    cfg = {}
    for k, default in DEFAULTS.items():
        v = raw.get(k, default)
        cfg[k] = {**default, **v} if isinstance(default, dict) and default and isinstance(v, dict) else v
    cfg["_dir"] = path.resolve().parent
    i18n.set_lang(cfg["lang"])
    terms.add_stop(cfg["stop_words"])
    settings.configure(cfg)
    return cfg


def known(cfg: dict, term: str) -> str:
    """The entry of known_terms that already covers this term, if any: what you have a
    page for, or never want reported."""
    for k in cfg["known_terms"]:
        k = k.lower()
        if k and (k in term or term in k):
            return k
    return ""
