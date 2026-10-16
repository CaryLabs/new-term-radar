from radar import sources, aisa, snap


def test_x_one_account_per_request(cfg, tmp_path, monkeypatch):
    cfg['x_accounts'] = {'labs': ['OpenAI', 'AnthropicAI'], 'bloggers': ['OpenAI']}
    calls = []
    def respond(batch):
        calls.append(batch)
        return {batch[0]['call_id']: {'data': {'tweets': []}}}, 3000
    monkeypatch.setattr(aisa, 'call', respond)
    result = sources.x_new(cfg, tmp_path)
    assert [len(batch) for batch in calls] == [1, 1]
    assert result['answered'] == 2
    assert result['cost_micros'] == 6000
    assert 'error' not in result


def test_x_stops_after_504_preserves_snapshot_and_known_cost(cfg, tmp_path, monkeypatch):
    cfg['x_accounts'] = {'labs': ['one', 'two', 'three'], 'bloggers': []}
    path = tmp_path / 'x_vocab.json.gz'
    snap.save(path, {'prior tool': '2026-10-01'})
    before = path.read_bytes()
    calls = []
    def respond(batch):
        name = batch[0]['call_id']
        calls.append(name)
        if name == 'two':
            raise aisa.AisaError('HTTP 504: Gateway timeout')
        return {name: {'data': {'tweets': []}}}, 3000
    monkeypatch.setattr(aisa, 'call', respond)
    result = sources.x_new(cfg, tmp_path)
    assert calls == ['one', 'two']
    assert result['answered'] == 1 and result['cost_micros'] == 3000
    assert result['failed_request_cost_unknown'] is True
    assert '504' in result['error']
    assert path.read_bytes() == before


def test_x_missing_tool_result_is_failure(cfg, tmp_path, monkeypatch):
    cfg['x_accounts'] = {'labs': ['one'], 'bloggers': []}
    monkeypatch.setattr(aisa, 'call', lambda batch: ({}, 0))
    result = sources.x_new(cfg, tmp_path)
    assert result['error']
    assert not (tmp_path / 'x_vocab.json.gz').exists()
