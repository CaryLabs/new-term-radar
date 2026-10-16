"""X timeline and search adapters; cost estimates are separate from the ledger."""
import urllib.parse
from datetime import datetime, timezone, timedelta

from .. import settings
from . import transport
from .errors import ProviderError


def normalize(tweet):
    author = tweet.get('author') or {}
    text = tweet.get('text')
    created = tweet.get('createdAt', tweet.get('created_at'))
    ident = str(tweet.get('id') or '')
    likes = tweet.get('likeCount', tweet.get('favorite_count'))
    username = author.get('userName', author.get('username'))
    if not ident or not isinstance(text, str) or not isinstance(created, str) or likes is None or not isinstance(username,str) or not username:
        raise ProviderError('X response missing required id/text/date/likes')
    try:
        dt = datetime.strptime(created, '%a %b %d %H:%M:%S %z %Y')
    except ValueError:
        try:
            dt = datetime.fromisoformat(created.replace('Z','+00:00'))
            if dt.tzinfo is None: raise ValueError()
        except ValueError:
            raise ProviderError('X response has invalid timestamp') from None
    if tweet.get('is_retweet') and not text.startswith('RT @'):
        text = 'RT @' + (username or '?') + ': ' + text
    return {'id':ident, 'text':text, 'createdAt':dt.strftime('%a %b %d %H:%M:%S %z %Y'),
            'likeCount':int(likes), 'url':tweet.get('url') or f'https://x.com/{username or "i"}/status/{ident}',
            'author':{'userName':username or '?'}, '_date':dt}


def _page(operation, params):
    provider = settings.option('providers', {}).get('x', {}).get('name', 'twitterapis')
    if provider == 'twitterapis':
        key = transport.credential('twitterapis_api_key')
        endpoint = 'user/tweets' if operation == 'timeline' else 'tweet/advanced_search'
        headers = {'Authorization':'Bearer '+key}
        price = 800
        base = 'https://api.twitterapis.com/twitter/'
    elif provider == 'twitterapi_io':
        key = transport.credential('twitterapi_io_api_key')
        endpoint = 'user/last_tweets' if operation == 'timeline' else 'tweet/advanced_search'
        params = dict(params)
        if 'username' in params: params['userName'] = params.pop('username')
        if 'product' in params: params['queryType'] = params.pop('product')
        headers = {'X-API-Key':key}
        base = 'https://api.twitterapi.io/twitter/'
        price = None
    else:
        raise ProviderError('Unsupported X provider')
    data, ticket = transport.request(provider, operation, base+endpoint+'?'+urllib.parse.urlencode(params), headers=headers)
    payload = data.get('data', data)
    tweets = payload.get('tweets') if isinstance(payload, dict) else None
    if not isinstance(tweets, list):
        transport.record(ticket, 'invalid_schema')
        raise ProviderError('X response missing tweets array')
    rows = [normalize(tw) for tw in tweets]
    # Sticker-price estimate, not reconciled cash spend. Ledger stays unknown.
    estimate = price if price is not None else max(1,len(rows))*150
    transport.record(ticket, 'ok', usage={'items':len(rows), 'estimated_cost_micros':estimate})
    cursor = payload.get('next_cursor') or data.get('next_cursor') or ''
    more = payload.get('has_next_page', data.get('has_next_page', bool(cursor)))
    return rows, cursor if more else '', estimate


def timeline(account):
    options = settings.option('providers', {}).get('x', {})
    cutoff = datetime.now(timezone.utc)-timedelta(hours=30)
    cursor, seen, rows, cost = '', set(), [], 0
    max_pages = options.get('max_pages', 5)
    for _ in range(max_pages):
        page, following, spent = _page('timeline', {'username':account, **({'cursor':cursor} if cursor else {})})
        cost += spent
        rows.extend(page)
        if not following or page and all(t['_date'] < cutoff for t in page):
            break
        if following in seen: raise ProviderError('X repeated cursor; timeline incomplete')
        seen.add(following); cursor=following
    else:
        raise ProviderError('X page budget reached before timeline window completed')
    unique = {t['id']:t for t in rows}
    for row in unique.values():row.pop('_date', None)
    return {'data':{'tweets':list(unique.values())}}, cost


def search(query, sort='Top'):
    page, cursor, spent = _page('search', {'query':query,'product':sort})
    for row in page:row.pop('_date',None)
    # Existing evidence gathering deliberately samples one search page.
    return {'tweets':page, 'next_cursor':cursor, 'sampled':bool(cursor)}, spent
