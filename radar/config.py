"""config.json: what to watch. Copy config.example.json and edit it.

Everything has a default except the X accounts and the sitemaps, which only you can
choose. Credentials and service addresses come only from this local JSON file.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import i18n, settings, terms

DEFAULTS = {
    "schema_version": 2,
    "providers": {"llm": {"name": "deepseek", "model": "deepseek-flash"},
                  "x": {"name": "twitterapis", "max_pages": 5}, "seo": {"name": "dataforseo"}},
    "limits": {"network_enabled": False, "daily_requests": 100, "monthly_requests": 3000, "cache_ttl_seconds": 86400},
    "lang": "en",
    "x_accounts": {"labs": [], "bloggers": []},
    "sitemaps": {},
    "topics": {},
    "known_terms": [],
    "stop_words": [],
    "judge": {"model": "deepseek-flash", "min_score": 0.5},
    "breakout": {"window_days": 14, "min_stars": 300, "velocity_min": 200, "delta_min": 400},
    "new_sites": {"queries": {"ai": "%ai%"}, "weekday": 0, "window_days": 90, "min_etv": 1000, "min_keywords": 20},
    "review": {"after_days": 14, "per_day": 5},
    "usecases": {"per_day": 5, "model": "deepseek-flash", "min_volume": 50, "trends_max": 10, "recheck_days": 3,
                 "location_code": 2840, "benchmark": "gpts", "min_daily": 300, "related": True, "related_geo": "US",
                 "country_trends": True, "country_min_volume": 1000, "country_max": 8},
    "competition": {"max_rows": 8, "weak_dr": 30, "location_code": 2840},
    "revenue": {"weekday": 0, "pages_growth": 3, "pages_new": 3, "min_revenue_usd": 500, "category": "", "max_leads": 10},
    "asks": {"weekday": 0, "time": "week", "min_score": 2, "model": "deepseek-flash", "min_volume": 50, "max_leads": 12,
             "location_code": 2840, "patterns": [
                 '"is there an ai tool"', '"is there an ai that"', '"is there a tool that"', '"any ai tool for"',
                 '"looking for an ai tool"', '"i wish there was a tool"', '"is there a way to automatically"',
                 '"how do i automate"', '"tool that can automatically"', '"recommend an ai"', '"best ai tool for"',
                 '"ai tool that can"']},
    "pains": {"model": "deepseek-flash", "extensions": 5, "review_pages": 2, "max_stars": 3, "reddit_time": "year", "videos": 3,
              "reddit_queries": ["{k} alternative", "{k} frustrating", '"{k}" "doesn\'t work"', "{k} wish there was"]},
    "tutorials": {"max_leads": 3, "videos": 3, "model": "deepseek-flash"},
    "gsc": {},
    "credentials": {"deepseek_api_key": "", "twitterapis_api_key": "", "twitterapi_io_api_key": "",
                    "dataforseo_login": "", "dataforseo_password": "", "reddit_client_id": "", "reddit_client_secret": "",
                    "youtube_api_key": "", "goanyapi_api_key": "", "github_token": "", "trustmrr_api_key": "",
                    "resend_api_key": "", "email_from": "", "email_to": []},
    "services": {"goanyapi_base_url": "https://api.goanyapi.com"},
}


def load(path: Path, providers_path: Path | None = None) -> dict:
    if not path.exists():
        raise SystemExit(f"{path} not found: copy config.example.json to {path.name} and edit it")
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError("config must be a JSON object")
    if providers_path is not None:
        overlay = json.loads(providers_path.read_text(encoding='utf-8-sig'))
        allowed = {'providers', 'credentials', 'services', 'limits'}
        if not isinstance(overlay, dict) or overlay.keys() - allowed:
            raise ValueError('Provider configuration supports only providers/credentials/services/limits')
        for group, values in overlay.items():
            if not isinstance(values, dict):
                raise ValueError('Provider configuration groups must be objects')
        # Legacy credentials stay on disk for the old checkout, never reach new providers.
        for group in ('credentials', 'services'):
            values = raw.get(group, {})
            if not isinstance(values, dict):
                raise ValueError('Invalid base configuration group')
            raw[group] = {k:v for k,v in values.items() if k in DEFAULTS[group]}
        for group, values in overlay.items():
            raw[group] = {**raw.get(group, {}), **values}
        raw['schema_version'] = 2
        for task in ('judge', 'usecases', 'asks', 'pains', 'tutorials'):
            raw[task] = {**raw.get(task, {}), 'model': overlay.get('providers', {}).get('llm', {}).get('model', DEFAULTS['providers']['llm']['model'])}
    legacy_credentials = raw.get('credentials', {})
    legacy_services = raw.get('services', {})
    if (isinstance(legacy_credentials, dict) and 'aisa_api_key' in legacy_credentials or
            isinstance(legacy_services, dict) and any(k.startswith('aisa_') for k in legacy_services)):
        raise ValueError('Legacy gateway configuration: run migrate-config to a separate local file')
    for group in ("credentials", "services"):
        values = raw.get(group, {})
        if not isinstance(values, dict):
            raise ValueError(f"{group} must be an object")
        unknown = values.keys() - DEFAULTS[group].keys()
        if unknown:
            raise ValueError(f"unknown {group} field(s); inspect local configuration")
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
    if cfg['schema_version'] != 2:
        raise ValueError('Unsupported config schema_version; expected 2')
    if not isinstance(cfg['providers'], dict) or not isinstance(cfg['limits'], dict):
        raise ValueError('providers and limits must be objects')
    for name, allowed in (('llm', ('deepseek',)), ('x', ('twitterapis','twitterapi_io')), ('seo', ('dataforseo',))):
        if not isinstance(cfg['providers'].get(name), dict) or cfg['providers'][name].get('name') not in allowed:
            raise ValueError(f'Unsupported providers.{name}')
    pages = cfg['providers']['x'].get('max_pages', 5)
    if type(pages) is not int or not 1 <= pages <= 20:
        raise ValueError('providers.x.max_pages must be 1..20')
    if type(cfg['limits'].get('network_enabled')) is not bool or any(type(cfg['limits'].get(k)) is not int or cfg['limits'][k] < 0 for k in ('daily_requests','monthly_requests')):
        raise ValueError('Invalid persistent request limits')
    if type(cfg['limits'].get('cache_ttl_seconds')) is not int or not 0 <= cfg['limits']['cache_ttl_seconds'] <= 604800:
        raise ValueError('cache_ttl_seconds must be 0..604800')
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
