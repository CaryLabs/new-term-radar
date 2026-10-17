"""Preflight and launch the normal CLI using local file settings only."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from . import __main__ as cli, config, settings


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv) or ["daily"]
    if "--help" in args or "-h" in args:
        if args[0] != "check":
            return cli.main(args)
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("command", choices=["check", "daily", "sources", "keywords", "leads", "pains", "mcp"])
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--out")
    parser.add_argument("--mail", action="store_true")
    opts, _ = parser.parse_known_args(args)
    try:
        if sys.version_info < (3, 10):
            raise ValueError("Python 3.10 or newer is required")
        if opts.command != "leads":
            cfg = config.load(Path(opts.config))
            if not settings.credential("aisa_api_key"):
                raise ValueError("fill credentials.aisa_api_key in the local config file before full-mode startup")
            for key in ("goanyapi_api_key", "trustmrr_api_key"):
                if not settings.credential(key):
                    print(f"Optional integration disabled: credentials.{key} is empty", file=sys.stderr)
            if cfg["gsc"].get("site"):
                token = cfg["_dir"] / cfg["gsc"].get("token_file", "gsc_token.json")
                if not token.is_file():
                    raise ValueError("configured GSC token_file does not exist")
        if opts.command == "mcp" and importlib.util.find_spec("mcp") is None:
            raise ValueError("MCP dependency missing: run the startup script with setup")
        if opts.mail:
            if importlib.util.find_spec("markdown") is None:
                raise ValueError("mail dependency missing: run the startup script with setup")
            if not all(settings.credential(k) for k in ("resend_api_key", "email_from")) or not settings.recipients_value():
                raise ValueError("mail requires credentials.resend_api_key, email_from and email_to")
        if opts.command == "check":
            print("Configuration OK (file-only; no network requests made).")
            return 0
        out = Path(opts.out) if opts.out else None
        if opts.command in ("daily", "sources") and out is None:
            out = Path("reports") / ("report.md" if opts.command == "daily" else "sources.md")
            out.parent.mkdir(parents=True, exist_ok=True)
            args += ["--out", str(out)]
        if opts.command != "mcp":
            print(f"Starting {opts.command}; config={Path(opts.config).resolve()}; credentials are read only from file", file=sys.stderr)
        result = cli.main(args)
        if opts.command == "daily" and out is not None and out.with_suffix(".json").exists():
            data = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
            failed = [k for k, v in data.items() if isinstance(v, dict) and (v.get("error") or v.get("errors"))]
            if failed:
                print("Run completed with incomplete data: " + ", ".join(failed), file=sys.stderr)
                return 3
        return result
    except (ValueError, OSError) as exc:
        print(f"Startup failed: {exc}", file=sys.stderr)
        return 2
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(f"Startup failed: {exc.code}", file=sys.stderr)
            return 2
        return int(exc.code or 0)


if __name__ == "__main__":
    raise SystemExit(main())
