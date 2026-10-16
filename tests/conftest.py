import copy

import pytest

from radar.providers import ProviderError
import urllib.request
from radar import config, goanyapi, i18n, settings


@pytest.fixture(autouse=True)
def english(monkeypatch):
    i18n.set_lang("en")
    settings.configure({})   # optional credentials are off unless a test configures them

    def no_network(*a, **k):
        raise goanyapi.GoAnyError("no network in tests")
    monkeypatch.setattr(goanyapi, "call", no_network)

    def no_paid_calls(*a, **k):       # a key on the machine must never turn a test into a paid call
        raise ProviderError("no network in tests")
    monkeypatch.setattr(urllib.request, "urlopen", no_paid_calls)
    monkeypatch.setattr(urllib.request, "build_opener", no_paid_calls)
    # The page-one check runs only in the tests that set it up, whatever loads the config (the MCP server too).
    monkeypatch.setitem(config.DEFAULTS["competition"], "max_rows", 0)
    monkeypatch.setitem(config.DEFAULTS["asks"], "weekday", None)          # weekly signals stay off unless a test asks
    monkeypatch.setitem(config.DEFAULTS["tutorials"], "max_leads", 0)


@pytest.fixture
def cfg(tmp_path):
    c = copy.deepcopy(config.DEFAULTS)
    c["_dir"] = tmp_path
    c["competition"]["max_rows"] = 0     # the page-one check runs only in the tests that set it up
    return c
