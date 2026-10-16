"""Direct DataForSEO Live endpoints, preserving native task data for pure rules."""
import base64
from decimal import Decimal, InvalidOperation

from . import transport
from .errors import ProviderError

PATHS = {'volume':'keywords_data/google_ads/search_volume/live',
         'trends':'keywords_data/google_trends/explore/live',
         'serp':'serp/google/organic/live/advanced',
         'difficulty':'dataforseo_labs/google/keyword_overview/live',
         'new_sites':'domain_analytics/whois/overview/live'}


def live(operation, params):
    login = transport.credential('dataforseo_login')
    password = transport.credential('dataforseo_password')
    token = base64.b64encode((login+':'+password).encode()).decode()
    data, ticket = transport.request('dataforseo', operation, 'https://api.dataforseo.com/v3/'+PATHS[operation],
                                     body=[params], headers={'Authorization':'Basic '+token})
    try:
        raw_cost = data.get('cost')
        cost = int(Decimal(str(raw_cost))*1_000_000) if raw_cost is not None else None
        if cost is not None and cost < 0: raise ValueError()
    except (InvalidOperation, ValueError, OverflowError):
        cost = None
    tasks = data.get('tasks')
    if data.get('status_code') != 20000 or not isinstance(tasks, list) or len(tasks)!=1 or tasks[0].get('status_code')!=20000:
        transport.record(ticket, 'provider_task_error', cost)
        raise ProviderError(f'DataForSEO {operation}: task failed; see provider console')
    if not isinstance(tasks[0].get('result'), list):
        transport.record(ticket,'no_data',cost)
        raise ProviderError(f'DataForSEO {operation}: no result data')
    transport.record(ticket, 'ok', cost)
    return data, (cost or 0) if ticket is not None else 0


def trends_many(queries):
    out, cost = {}, 0
    for query in queries:
        data, spent = live('trends', query['params'])
        out[query['id']] = data
        cost += spent
    return out, cost


def new_sites_many(queries):
    out, cost = {}, 0
    for query in queries:
        data, spent = live('new_sites',query['params'])
        out[query['id']] = data
        cost += spent
    return out,cost
