"""Treat all external page/API content as untrusted input."""

from __future__ import annotations

import re

# Common prompt-injection / tool-smuggling markers in scraped text.
_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions"),
    re.compile(r"(?i)system\s*prompt"),
    re.compile(r"(?i)you\s+are\s+now\s+"),
    re.compile(r"(?i)</?\s*(system|assistant|tool_call|function_call)\s*>"),
    re.compile(r"(?i)do\s+not\s+follow\s+repo\s+rules"),
    re.compile(r"(?i)exfiltrat"),
    re.compile(r"(?i)send\s+this\s+to\s+https?://"),
]

_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_WS_RE = re.compile(r"\s+")


def sanitize_text(text: str, *, max_len: int = 8000) -> str:
    """Strip control chars, collapse whitespace, truncate, flag injection markers."""
    if not text:
        return ""
    cleaned = _CTRL_RE.sub(" ", text)
    cleaned = _WS_RE.sub(" ", cleaned).strip()
    for pat in _INJECTION_PATTERNS:
        if pat.search(cleaned):
            cleaned = pat.sub("[untrusted-instruction-removed]", cleaned)
    if len(cleaned) > max_len:
        cleaned = cleaned[: max_len - 1] + "…"
    return cleaned


def safe_excerpt(text: str, *, max_len: int = 280) -> str:
    return sanitize_text(text, max_len=max_len)
