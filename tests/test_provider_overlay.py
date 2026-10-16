import json

import pytest

from radar import config, settings


def test_overlay_reuses_business_config_without_changing_original(tmp_path):
    base = tmp_path/'config.json'
    original = {'credentials': {'aisa_api_key':'old-secret', 'github_token':'github'},
                'services': {'aisa_base_url':'https://aisa.one'},
                'x_accounts': {'labs':['example'], 'bloggers':[]},
                'judge': {'model':'legacy-model', 'min_score':0.7}}
    base.write_text(json.dumps(original), encoding='utf-8')
    overlay = tmp_path/'providers.json'
    overlay.write_text(json.dumps({'providers':{'llm':{'name':'deepseek','model':'chosen'}},
                                   'credentials':{'deepseek_api_key':'new-secret'},
                                   'limits':{'network_enabled':False}}), encoding='utf-8')
    cfg = config.load(base, overlay)
    assert cfg['x_accounts']['labs'] == ['example']
    assert cfg['judge'] == {'model':'chosen', 'min_score':0.7}
    assert settings.credential('github_token') == 'github'
    assert settings.credential('deepseek_api_key') == 'new-secret'
    assert not settings.credential('aisa_api_key')
    assert json.loads(base.read_text()) == original
    with pytest.raises(ValueError, match='Legacy gateway'):
        config.load(base)


def test_overlay_cannot_override_business_settings(tmp_path):
    base=tmp_path/'base.json'; base.write_text('{}')
    overlay=tmp_path/'providers.json'; overlay.write_text('{"x_accounts":{}}')
    with pytest.raises(ValueError,match='only'):
        config.load(base,overlay)
