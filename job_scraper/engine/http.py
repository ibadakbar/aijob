"""Shared HTTP helpers with timeout, retries, and polite User-Agent."""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
from typing import Any, Optional

UA = "Mozilla/5.0 (compatible; visa-discover/1.0; personal job search; +https://github.com/)"


def fetch_json(
    url: str,
    *,
    timeout: float = 30.0,
    max_retries: int = 4,
    headers: Optional[dict[str, str]] = None,
) -> Any:
    hdrs = {"User-Agent": UA, "Accept": "application/json", **(headers or {})}
    delay = 0.5
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code == 404:
                raise
            if exc.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                time.sleep(delay + random.random() * 0.4)
                delay = min(delay * 2, 8.0)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = exc
            if attempt < max_retries:
                time.sleep(delay + random.random() * 0.4)
                delay = min(delay * 2, 8.0)
                continue
            raise
    raise RuntimeError(f"fetch failed for {url}: {last_err}")
