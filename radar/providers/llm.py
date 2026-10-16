from .. import settings
from . import transport
from .errors import ProviderError


def chat(model, system, user, max_tokens=1500):
    key = transport.credential('deepseek_api_key')
    chosen = settings.option('providers', {}).get('llm', {}).get('model', 'deepseek-flash')
    # Task-specific configured model names are honored; old model IDs must be migrated.
    model = chosen if not model or model == 'deepseek-flash' else model
    body = {'model': model, 'messages': [{'role':'system','content':system}, {'role':'user','content':user}],
            'max_tokens':max_tokens, 'stream':False, 'thinking': {'type':'disabled'}}
    data, ticket = transport.request('deepseek', 'chat', 'https://api.deepseek.com/chat/completions',
                                     body=body, headers={'Authorization': 'Bearer '+key})
    try:
        choice = data['choices'][0]
        content = choice['message']['content']
        if choice.get('finish_reason') != 'stop' or not isinstance(content, str) or not content.strip():
            raise ValueError()
    except (KeyError, IndexError, TypeError, ValueError):
        transport.record(ticket, 'invalid_or_truncated', usage=data.get('usage'))
        raise ProviderError('DeepSeek returned missing or truncated content; no retry') from None
    transport.record(ticket, 'ok', usage=data.get('usage'))
    return content
