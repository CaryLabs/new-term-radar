import io
import ssl
import urllib.error
import urllib.request

import pytest

from radar import aisa, http, settings
from radar.__main__ import run

REAL_POST = aisa._post


def test_public_get_recovers_transient_eof(monkeypatch):
    calls = []
    def respond(*args, **kwargs):
        calls.append(1)
        if len(calls) < 3:
            raise urllib.error.URLError(ssl.SSLEOFError("connection closed"))
        return io.BytesIO(b'{"ok": true}')
    monkeypatch.setattr(urllib.request, "urlopen", respond)
    monkeypatch.setattr(http.time, "sleep", lambda _: None)
    assert http.get_json(urllib.request.Request("https://example.com"), 1) == {"ok": True}
    assert len(calls) == 3


@pytest.mark.parametrize("failure", [
    urllib.error.HTTPError("https://example.com", 401, "unauthorized", {}, io.BytesIO()),
    urllib.error.URLError(ssl.SSLCertVerificationError("bad certificate")),
])
def test_public_get_does_not_retry_terminal_failures(monkeypatch, failure):
    calls = []
    def respond(*args, **kwargs):
        calls.append(1)
        raise failure
    monkeypatch.setattr(urllib.request, "urlopen", respond)
    with pytest.raises(OSError):
        http.get_json(urllib.request.Request("https://example.com"), 1)
    assert len(calls) == 1


def test_public_get_stops_after_three_failures(monkeypatch):
    calls = []
    def respond(*args, **kwargs):
        calls.append(1)
        raise TimeoutError("timeout")
    monkeypatch.setattr(urllib.request, "urlopen", respond)
    monkeypatch.setattr(http.time, "sleep", lambda _: None)
    with pytest.raises(TimeoutError):
        http.get_json(urllib.request.Request("https://example.com"), 1)
    assert len(calls) == 3


@pytest.mark.parametrize("code, hint", [(401, "Authentication rejected"), (402, "paid balance required")])
def test_aisa_account_failure_has_actionable_guidance_without_retry(monkeypatch, code, hint):
    settings.configure({"credentials": {"aisa_api_key": "test-secret"}})
    calls = []
    def respond(*args, **kwargs):
        calls.append(1)
        raise urllib.error.HTTPError("https://example.com", code, "rejected", {}, io.BytesIO(b'{}'))
    monkeypatch.setattr(urllib.request, "urlopen", respond)
    with pytest.raises(aisa.AisaError, match=hint) as error:
        REAL_POST("https://example.com", {}, 1)
    assert "test-secret" not in str(error.value)
    assert len(calls) == 1


def test_progress_marks_failure_and_skip(capsys):
    assert run(lambda: {"error": "failed"}, label="HF") == {"error": "failed"}
    assert "[HF] incomplete" in capsys.readouterr().err
    assert run(lambda: pytest.fail("must skip"), True, "skipped") == {"skipped": True}
    assert capsys.readouterr().err == ""


def test_progress_preserves_non_dict_result():
    assert run(lambda: 5, label="record") == 5


def test_get_rejects_post_before_network():
    with pytest.raises(ValueError, match="only accepts GET"):
        http.get_json(urllib.request.Request("https://example.com", data=b'{}'), 1)


def test_daily_persists_judge_failure_for_launcher(tmp_path, monkeypatch):
    import json
    from radar import __main__ as cli, launcher
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"credentials": {"aisa_api_key": "test-only"}}))
    monkeypatch.setattr(cli.report, "leads", lambda *args: ([], {"error": "HTTP 402: balance required"}))
    out = tmp_path / "report.md"
    result = launcher.main(["daily", "--config", str(config_file), "--state", str(tmp_path / "state"),
                            "--out", str(out), "--skip", ",".join(cli.SKIPPABLE)])
    assert result == 3
    data = json.loads(out.with_suffix(".json").read_text())
    assert data["judge"]["error"] == "HTTP 402: balance required"
