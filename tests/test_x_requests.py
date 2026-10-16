from radar import sources, snap
from radar.providers import x, ProviderError


def test_x_one_account_per_request(cfg, tmp_path, monkeypatch):
    cfg['x_accounts'] = {'labs': ['OpenAI', 'AnthropicAI'], 'bloggers': ['OpenAI']}
    calls = []
    def respond(account):
        calls.append(account)
        return {'data': {'tweets': []}}, 3000
    monkeypatch.setattr(x, 'timeline', respond)
    result = sources.x_new(cfg, tmp_path)
    assert calls == ['OpenAI', 'AnthropicAI']
    assert result['answered'] == 2
    assert result['cost_micros'] == 6000
    assert 'error' not in result


def test_x_stops_after_504_preserves_snapshot_and_known_cost(cfg, tmp_path, monkeypatch):
    cfg['x_accounts'] = {'labs': ['one', 'two', 'three'], 'bloggers': []}
    path = tmp_path / 'x_vocab.json.gz'
    snap.save(path, {'prior tool': '2026-10-01'})
    before = path.read_bytes()
    calls = []
    def respond(name):
        calls.append(name)
        if name == 'two':
            raise ProviderError('HTTP 504: Gateway timeout')
        return {'data': {'tweets': []}}, 3000
    monkeypatch.setattr(x, 'timeline', respond)
    result = sources.x_new(cfg, tmp_path)
    assert calls == ['one', 'two']
    assert result['answered'] == 1 and result['cost_micros'] == 3000
    assert result['failed_request_cost_unknown'] is True
    assert '504' in result['error']
    assert path.read_bytes() == before


def test_x_missing_tool_result_is_failure(cfg, tmp_path, monkeypatch):
    cfg['x_accounts'] = {'labs': ['one'], 'bloggers': []}
    monkeypatch.setattr(x, 'timeline', lambda batch: ({}, 0))
    result = sources.x_new(cfg, tmp_path)
    assert result['error']
    assert not (tmp_path / 'x_vocab.json.gz').exists()
