"""Fixed-origin HTTP with persistent request limits and sanitized usage records."""
import json
import hashlib
import sqlite3
import time
from contextlib import contextmanager
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import settings
from .errors import ProviderError

HOSTS = {'api.deepseek.com', 'api.twitterapis.com', 'api.twitterapi.io', 'api.goanyapi.com',
         'api.dataforseo.com', 'oauth.reddit.com', 'www.reddit.com', 'www.googleapis.com'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


@contextmanager
def database():
    path = Path(settings.option('usage_path', 'state/provider-usage.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute('CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY, day TEXT, provider TEXT, operation TEXT, status TEXT, cost INTEGER, usage TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, expires REAL, data TEXT)')
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def reserve(provider, operation):
    limits = settings.option('limits', {})
    if not limits.get('network_enabled', False):
        raise ProviderError('Network disabled in local limits configuration')
    day = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
    with database() as conn:
        conn.execute('BEGIN IMMEDIATE')
        daily = conn.execute("SELECT COUNT(*) FROM requests WHERE day=? AND status!='cache_hit'", (day,)).fetchone()[0]
        monthly = conn.execute("SELECT COUNT(*) FROM requests WHERE day LIKE ? AND status!='cache_hit'", (day[:7]+'%',)).fetchone()[0]
        if daily >= limits.get('daily_requests', 0) or monthly >= limits.get('monthly_requests', 0):
            raise ProviderError('Persistent request budget exhausted')
        row = conn.execute('INSERT INTO requests(day,provider,operation,status) VALUES (?,?,?,?)',
                           (day, provider, operation, 'reserved'))
        return row.lastrowid


def record(ticket, status, cost=None, usage=None):
    if ticket is None:
        return
    with database() as conn:
        conn.execute('UPDATE requests SET status=?,cost=?,usage=? WHERE id=?',
                     (status, cost, json.dumps(usage or {}), ticket))


def summary():
    with database() as conn:
        rows = conn.execute('SELECT provider,COUNT(*),COALESCE(SUM(cost),0),SUM(cost IS NULL) FROM requests GROUP BY provider').fetchall()
    return {'providers': [{'provider': p, 'requests': n, 'known_cost_micros': c, 'unknown_cost_requests': u}
                          for p,n,c,u in rows], 'note': 'Known costs only; unknown fees are not zero. Lifetime ledger, not a per-run bill.'}


def request(provider, operation, url, *, body=None, headers=None, form=None):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in HOSTS or parsed.username or parsed.password or parsed.fragment:
        raise ProviderError('Unapproved provider origin')
    # Tokens are never cached; live X timelines are not cached either. Cache keys
    # exclude authorization and URL credentials, and the ledger is scoped to state.
    ttl = settings.option('limits', {}).get('cache_ttl_seconds', 86400)
    cacheable = operation not in ('token','timeline','search') and ttl > 0
    clean_query = [(k,v) for k,v in urllib.parse.parse_qsl(parsed.query) if k.lower() not in ('key','api_key','access_token')]
    cache_key = hashlib.sha256(json.dumps([provider,operation,parsed.path,clean_query,body,form],sort_keys=True).encode()).hexdigest()
    if cacheable:
        with database() as conn:
            cached=conn.execute('SELECT data FROM cache WHERE key=? AND expires>?',(cache_key,time.time())).fetchone()
        if cached:
            return json.loads(cached[0]), None
    payload = None
    hdr = {'User-Agent': 'new-term-radar/1.0 (independent-provider client)', **(headers or {})}
    if body is not None:
        payload = json.dumps(body).encode()
        hdr['Content-Type'] = 'application/json'
    if form is not None:
        payload = urllib.parse.urlencode(form).encode()
        hdr['Content-Type'] = 'application/x-www-form-urlencoded'
    ticket = reserve(provider, operation)
    req = urllib.request.Request(url, data=payload, headers=hdr)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=90) as response:
            data = json.load(response)
        if not isinstance(data, dict):
            raise ValueError('Invalid response')
        record(ticket, 'received')
        # Only cache provider-level successful replies; task errors/partial
        # completions must remain retryable by a later explicit user run.
        good = not data.get('error')
        if provider == 'dataforseo':
            good = good and data.get('status_code') == 20000 and bool(data.get('tasks')) and all(t.get('status_code')==20000 for t in data['tasks'])
        if provider == 'deepseek':
            good = good and bool(data.get('choices')) and data['choices'][0].get('finish_reason')=='stop'
        if cacheable and good:
            with database() as conn:
                conn.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)',(cache_key,time.time()+ttl,json.dumps(data)))
        return data, ticket
    except urllib.error.HTTPError as exc:
        record(ticket, f'http_{exc.code}')
        raise ProviderError(f'{provider}/{operation}: HTTP {exc.code}; no retry; fee unknown') from None
    except (OSError, ValueError):
        record(ticket, 'transport_error')
        raise ProviderError(f'{provider}/{operation}: network or invalid JSON; no retry; fee unknown') from None


def credential(name):
    key = settings.credential(name)
    if not key:
        raise ProviderError(f'Missing credentials.{name} in local JSON configuration')
    return key
