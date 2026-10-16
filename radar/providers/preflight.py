from .. import settings


def required(command, skip=()):
    skip=set(skip)
    keys=[]
    if command in ('check','daily','sources','keywords','pains','mcp'):
        if 'judge' not in skip or command in ('keywords','pains','mcp','check'):
            keys.append('deepseek_api_key')
    if command in ('check','mcp','keywords') or command in ('daily','sources') and 'x' not in skip:
        provider=settings.option('providers',{}).get('x',{}).get('name','twitterapis')
        keys.append('twitterapis_api_key' if provider=='twitterapis' else 'twitterapi_io_api_key')
    if command in ('check','mcp','keywords') or command=='daily' and any(k not in skip for k in ('newsites','review','asks','usecases')):
        keys += ['dataforseo_login','dataforseo_password']
    if command in ('check','mcp','pains') or command=='daily' and 'asks' not in skip:
        keys += ['reddit_client_id','reddit_client_secret']
    if command in ('check','mcp','pains') or command=='daily' and 'tutorials' not in skip:
        keys.append('youtube_api_key')
    if command=='daily' and any(k not in skip for k in ('judge','usecases','asks','tutorials')):
        keys.append('deepseek_api_key')
    return sorted(set(keys))


def check(command,skip=()):
    needed=required(command,skip)
    missing=[k for k in needed if not settings.credential(k)]
    if missing:raise ValueError('Missing local credentials: '+', '.join('credentials.'+k for k in missing))
    if command!='check' and needed and not settings.option('limits',{}).get('network_enabled',False):
        raise ValueError('Provider network disabled; explicitly set limits.network_enabled=true before a live run')
