"""File-loaded service settings, scoped to the current invocation/context.

No environment, .env or per-user CLI credential fallback is used.
asyncio.to_thread inherits this context; loading another config replaces it.
"""
from __future__ import annotations

from contextvars import ContextVar, copy_context

_active: ContextVar[dict] = ContextVar("radar_file_settings", default={})


def configure(cfg: dict) -> None:
    _active.set({"credentials": dict(cfg.get("credentials", {})), "services": dict(cfg.get("services", {}))})


def credential(name: str) -> str:
    value = _active.get().get("credentials", {}).get(name, "")
    return value.strip() if isinstance(value, str) else ""


def recipients_value() -> str:
    value = _active.get().get("credentials", {}).get("email_to", [])
    return ",".join(value) if isinstance(value, list) else value


def service(name: str, default: str) -> str:
    return _active.get().get("services", {}).get(name, default).rstrip("/")


def inherit_context(fn):
    """Bind settings before submitting work to a plain ThreadPoolExecutor."""
    context = copy_context()
    def bound(*args, **kwargs):
        return context.copy().run(fn, *args, **kwargs)
    return bound
