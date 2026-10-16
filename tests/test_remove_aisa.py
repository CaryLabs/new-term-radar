import ast
import copy
import importlib.util
import json
import sqlite3
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from radar import config, settings, migrate_config, run_lock
from radar.providers import ProviderError, guard, llm, seo, social, transport, x


@pytest.fixture
def context(tmp_path):
    cfg=copy.deepcopy(config.DEFAULTS)
    cfg['_dir']=tmp_path
    cfg['credentials'].update({k:'test-secret' for k in cfg['credentials'] if k!='email_to'})
    cfg['limits'].update(network_enabled=True,daily_requests=10,monthly_requests=20,cache_ttl_seconds=0)
    settings.configure(cfg)
    return cfg


def stub(monkeypatch, data):
    calls=[]
    def request(*args, **kwargs):
        calls.append((args,kwargs))
        return data, 1
    monkeypatch.setattr(transport,'request',request)
    monkeypatch.setattr(transport,'record',lambda *a, **k:None)
    return calls


def tweet(ident='1'):
    return {'id':ident,'text':'A new tool','created_at':datetime.now(timezone.utc).strftime('%a %b %d %H:%M:%S %z %Y'),
            'favorite_count':5,'author':{'username':'OpenAI'}}


def test_zero_aisa_imports_in_production():
    root=Path(__file__).resolve().parents[1]/'radar'
    assert not (root/'aisa.py').exists()
    for path in root.rglob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all('aisa' not in n.name.split('.') for n in node.names),path
            if isinstance(node, ast.ImportFrom):
                assert 'aisa' not in (node.module or '').split('.'),path
                assert all(n.name!='aisa' for n in node.names),path


@pytest.mark.parametrize('url',['https://tools.aisa.one/path','https://api.aisa.one/x','https://aisa.one/'])
def test_zero_aisa_negative_network_audit(url):
    guard.install()
    with pytest.raises(ProviderError,match='forbidden'):
        sys.audit('urllib.Request',url,None,{},'GET')
    with pytest.raises(ProviderError):
        transport.request('fake','call',url)


def test_network_disabled_before_any_request(tmp_path):
    settings.configure({'_dir':tmp_path,'limits':{'network_enabled':False}})
    with pytest.raises(ProviderError,match='disabled'):
        transport.request('deepseek','chat','https://api.deepseek.com/chat/completions')


def test_persistent_request_budget_and_unknown_fees(context):
    context['limits']['daily_requests']=1
    settings.configure(context)
    ticket=transport.reserve('test','one')
    transport.record(ticket,'http_504')
    settings.configure(context)  # reset context is not reset quota
    with pytest.raises(ProviderError,match='budget exhausted'):transport.reserve('test','two')
    assert transport.summary()['providers']==[{'provider':'test','requests':1,'known_cost_micros':0,'unknown_cost_requests':1}]


def test_month_budget_counts_previous_days(context):
    context['limits']['monthly_requests']=1
    settings.configure(context)
    transport.reserve('test','one')
    with transport.database() as conn:
        conn.execute("UPDATE requests SET day=substr(day,1,7)||'-01'")
    with pytest.raises(ProviderError,match='budget exhausted'):transport.reserve('test','two')


def test_no_redirect():
    assert transport.NoRedirect().redirect_request(None,None,None,None,None,None) is None


def test_http_error_redacts_key_and_no_retry(context,monkeypatch):
    opener=MagicMock()
    opener.open.side_effect=urllib.error.HTTPError('https://host/?key=secret',504,'secret',{},None)
    monkeypatch.setattr('urllib.request.build_opener',lambda *a:opener)
    with pytest.raises(ProviderError) as err:
        transport.request('youtube','comments','https://www.googleapis.com/youtube/v3/commentThreads?key=secret')
    assert 'secret' not in str(err.value) and '504' in str(err.value)
    assert opener.open.call_count==1


def test_cache_reuses_result_without_charging(context,monkeypatch):
    context['limits']['cache_ttl_seconds']=60
    settings.configure(context)
    response=MagicMock()
    response.__enter__.return_value.read.return_value=json.dumps({'choices':[{'finish_reason':'stop','message':{'content':'ok'}}]}).encode()
    opener=MagicMock();opener.open.return_value=response
    monkeypatch.setattr('urllib.request.build_opener',lambda *a:opener)
    first,ticket=transport.request('deepseek','chat','https://api.deepseek.com/chat/completions',body={'model':'m'})
    again,second=transport.request('deepseek','chat','https://api.deepseek.com/chat/completions',body={'model':'m'})
    assert first==again and ticket is not None and second is None
    assert opener.open.call_count==1


def test_llm_sends_direct_and_checks_truncation(context,monkeypatch):
    calls=stub(monkeypatch,{'choices':[{'finish_reason':'length','message':{'content':'partial'}}]})
    with pytest.raises(ProviderError,match='truncated'):llm.chat('deepseek-flash','system','text')
    assert calls[0][0][2]=='https://api.deepseek.com/chat/completions'
    assert calls[0][1]['body']['thinking']=={'type':'disabled'}


def test_llm_configured_model(context,monkeypatch):
    context['providers']['llm']['model']='other-deepseek-model'
    settings.configure(context)
    calls=stub(monkeypatch,{'choices':[{'finish_reason':'stop','message':{'content':'ok'}}]})
    assert llm.chat('deepseek-flash','s','u')=='ok'
    assert calls[0][1]['body']['model']=='other-deepseek-model'


def test_x_normalized_timeline(context,monkeypatch):
    calls=stub(monkeypatch,{'tweets':[tweet()],'next_cursor':''})
    data,cost=x.timeline('OpenAI')
    row=data['data']['tweets'][0]
    assert row['id']=='1' and row['likeCount']==5 and row['author']['userName']=='OpenAI'
    assert cost==800 and calls[0][0][0]=='twitterapis'


def test_x_io_search_adapter(context,monkeypatch):
    context['providers']['x']['name']='twitterapi_io';settings.configure(context)
    calls=stub(monkeypatch,{'tweets':[tweet()],'has_next_page':False})
    data,cost=x.search('test','Latest')
    assert len(data['tweets'])==1 and cost==150
    assert 'queryType=Latest' in calls[0][0][2] and 'X-API-Key' in calls[0][1]['headers']


def test_x_pagination_cap_is_not_success(context,monkeypatch):
    context['providers']['x']['max_pages']=1;settings.configure(context)
    stub(monkeypatch,{'tweets':[tweet()],'next_cursor':'next'})
    with pytest.raises(ProviderError,match='incomplete|budget'):x.timeline('OpenAI')


def test_x_missing_likes_not_zero():
    value=tweet();value.pop('favorite_count')
    with pytest.raises(ProviderError):x.normalize(value)


@pytest.mark.parametrize('operation',list(seo.PATHS))
def test_each_seo_capability_has_direct_endpoint(operation,context,monkeypatch):
    calls=stub(monkeypatch,{'status_code':20000,'cost':0.0012,'tasks':[{'status_code':20000,'result':[]}]})
    data,cost=seo.live(operation,{'keywords':['a']})
    assert cost==1200 and len(calls)==1
    assert calls[0][0][2]=='https://api.dataforseo.com/v3/'+seo.PATHS[operation]
    assert calls[0][1]['body']==[{'keywords':['a']}]
    assert calls[0][1]['headers']['Authorization'].startswith('Basic ')


def test_seo_task_failure_not_empty(context,monkeypatch):
    stub(monkeypatch,{'status_code':20000,'tasks':[{'status_code':40501,'result':None}]})
    with pytest.raises(ProviderError):seo.live('volume',{})


def test_reddit_oauth_and_search(context,monkeypatch):
    calls=[]
    data={'data':{'children':[{'data':{'id':'p','title':'Need tool','selftext':'hello','score':7,'subreddit':'test','permalink':'/r/test/p','created_utc':1}}]}}
    def request(provider,operation,url,**kwargs):
        calls.append((operation,url))
        return ({'access_token':'temporary-token'} if operation=='token' else data),1
    monkeypatch.setattr(transport,'request',request);monkeypatch.setattr(transport,'record',lambda *a,**k:None)
    rows,cost=social.reddit('is there a tool')
    assert rows[0]['score']==7 and rows[0]['url']=='https://www.reddit.com/r/test/p'
    assert [r[0] for r in calls]==['token','search']


def test_youtube_top_level_comments(context,monkeypatch):
    stub(monkeypatch,{'items':[{'snippet':{'topLevelComment':{'id':'c','snippet':{'textDisplay':'help &amp; thanks','likeCount':4}}}}]})
    rows,cost=social.youtube_comments('video')
    assert rows==[{'id':'c','text':'help & thanks','likes':4}]


def test_migration_preserves_source_and_does_not_copy_gateway_key(tmp_path):
    source=tmp_path/'source.json';out=tmp_path/'new.json'
    source.write_text(json.dumps({'credentials':{'aisa_api_key':'private-old','github_token':'keep'},'lang':'zh'}))
    before=source.read_bytes()
    assert migrate_config.main(['--input',str(source),'--out',str(out)])==0
    migrated=json.loads(out.read_text(encoding='utf-8'))
    assert 'private-old' not in out.read_text() and migrated['credentials']['github_token']=='keep'
    assert migrated['limits']['network_enabled'] is False
    assert source.read_bytes()==before
    assert migrate_config.main(['--input',str(source),'--out',str(out)])==2


def test_old_config_fails_closed(tmp_path):
    p=tmp_path/'config.json';p.write_text('{"credentials":{"aisa_api_key":"secret"}}')
    with pytest.raises(ValueError,match='migrate'):config.load(p)


def test_state_lock_rejects_concurrent_writer(tmp_path):
    with run_lock.hold(tmp_path):
        with pytest.raises(ValueError,match='Another process'):
            with run_lock.hold(tmp_path):pass
    with run_lock.hold(tmp_path):pass
