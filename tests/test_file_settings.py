"""File configuration and launch boundaries; all credentials are fake test values."""
import asyncio
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from radar import aisa, competition, config, goanyapi, launcher, settings, usecases


def write_config(path, **values):
    path.write_text(json.dumps(values, ensure_ascii=False), encoding="utf-8-sig")
    return path


def test_file_credentials_ignore_legacy_environment_and_clear_on_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("AISA_API_KEY", "ignored-environment-secret")
    monkeypatch.setenv("GOANYAPI_API_KEY", "ignored-environment-secret")
    path = write_config(tmp_path / "配置.json", credentials={"aisa_api_key": "file-secret", "goanyapi_api_key": "optional-file"})
    config.load(path)
    assert aisa.key() == "file-secret" and goanyapi.key() == "optional-file"
    config.load(write_config(path))
    assert goanyapi.key() == ""
    with pytest.raises(aisa.AisaError, match="credentials.aisa_api_key"):
        aisa.key()


@pytest.mark.parametrize("value", [None, [], {"aisa_api_key": 42}, {"mistyped_key": "private-value"}])
def test_bad_credential_config_does_not_echo_values(tmp_path, value):
    path = write_config(tmp_path / "config.json", credentials=value)
    with pytest.raises(ValueError) as exc:
        config.load(path)
    assert "private-value" not in str(exc.value)


@pytest.mark.parametrize("url", ["http://plain.example", "https://user:secret@example.com", "https://example.com?key=secret"])
def test_service_urls_require_https_without_embedded_secrets(tmp_path, url):
    with pytest.raises(ValueError) as exc:
        config.load(write_config(tmp_path / "config.json", services={"aisa_api_base_url": url}))
    assert url not in str(exc.value)


def test_router_and_chat_endpoints_are_consumed_from_file(tmp_path, monkeypatch):
    config.load(write_config(tmp_path / "config.json", credentials={"aisa_api_key": "fake"}, services={
        "aisa_router_base_url": "https://router.example/", "aisa_api_base_url": "https://chat.example/"}))
    calls = []
    def post(url, body, timeout):
        calls.append(url)
        return {"results": [], "choices": [{"message": {"content": "ok"}}]}
    monkeypatch.setattr(aisa, "_post", post)
    aisa.call([{"call_id": "one"}])
    assert aisa.chat("test-model", "s", "u") == "ok"
    assert calls == ["https://router.example/v1/tool-router/aisa-batch-use", "https://chat.example/v1/chat/completions"]


def test_country_rating_and_supply_workers_inherit_file_credentials(tmp_path, monkeypatch):
    settings.configure({"credentials": {"goanyapi_api_key": "thread-secret"}})
    cfg = copy.deepcopy(config.DEFAULTS)
    observed = []
    def daily(*args):
        observed.append(goanyapi.key())
        return [], 0
    def call(path, **kwargs):
        observed.append(goanyapi.key())
        return {"domain_rating": 10, "intitleCount": 2, "domains": []}, 0
    monkeypatch.setattr(goanyapi, "daily_series", daily)
    monkeypatch.setattr(goanyapi, "call", call)
    usecases.country_series([{"phrase": "example", "kind": "name"}], cfg["usecases"])
    competition.ratings(["domain.example"], tmp_path)
    competition.supply([{"phrase": "example", "competition": {}}])
    assert observed == ["thread-secret"] * 4


def test_async_to_thread_uses_current_config_context():
    async def run():
        settings.configure({"credentials": {"aisa_api_key": "async-secret"}})
        return await asyncio.to_thread(aisa.key)
    assert asyncio.run(run()) == "async-secret"
    with pytest.raises(aisa.AisaError):
        aisa.key()  # the task-local credentials did not leak back into the caller


def test_launcher_refuses_missing_key_before_cli_or_network(tmp_path, monkeypatch, capsys):
    path = write_config(tmp_path / "config.json")
    def forbidden(*args):
        pytest.fail("CLI must not execute before full-mode key validation")
    monkeypatch.setattr(launcher.cli, "main", forbidden)
    assert launcher.main(["daily", "--config", str(path)]) == 2
    assert "credentials.aisa_api_key" in capsys.readouterr().err


def test_launcher_missing_config_is_a_preflight_failure(tmp_path, capsys):
    assert launcher.main(["check", "--config", str(tmp_path / "missing.json")]) == 2
    assert "Startup failed:" in capsys.readouterr().err


def test_launcher_reports_partial_daily_instead_of_false_success(tmp_path, monkeypatch):
    path = write_config(tmp_path / "config.json", credentials={"aisa_api_key": "fake"})
    out = tmp_path / "report.md"
    def partial(args):
        out.with_suffix(".json").write_text(json.dumps({"hf": {"error": "timeout"}}))
        return 0
    monkeypatch.setattr(launcher.cli, "main", partial)
    assert launcher.main(["daily", "--config", str(path), "--out", str(out)]) == 3


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Git Bash integration")
def test_windows_bash_script_handles_other_working_directory_and_spaced_config(tmp_path):
    bash = Path("C:/Program Files/Git/bin/bash.exe")
    if not bash.exists():
        pytest.skip("Git Bash not installed")
    root = Path(__file__).resolve().parents[1]
    if not (root / ".venv/Scripts/python.exe").exists():
        pytest.skip("startup virtual environment not installed")
    path = write_config(tmp_path / "local config.json", credentials={"aisa_api_key": "script-test-secret"})
    result = subprocess.run([str(bash), str(root / "scripts/start-windows.sh"), "check", "--config", str(path)],
                            cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stderr
    assert "Configuration OK" in result.stdout
    assert "script-test-secret" not in result.stdout + result.stderr
