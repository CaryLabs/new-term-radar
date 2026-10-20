"""Bounded retries for idempotent public GET requests only."""
from __future__ import annotations

import ssl
import time
import urllib.error
import urllib.request


def get_json(request: urllib.request.Request, timeout: int):
    import json

    if request.get_method() != "GET":
        raise ValueError("get_json only accepts GET requests")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except OSError as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, ssl.SSLCertVerificationError):
                raise
            if isinstance(exc, urllib.error.HTTPError) and exc.code != 429 and not 500 <= exc.code < 600:
                raise
            if attempt == 2:
                raise
            if isinstance(exc, urllib.error.HTTPError):
                exc.close()
            time.sleep(attempt + 1)
