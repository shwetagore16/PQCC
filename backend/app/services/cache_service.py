"""Simple in-memory cache for PQC analysis results."""

from __future__ import annotations

import json
import time
from typing import Any

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_DEFAULT_TTL_SECONDS = 900


def _now() -> float:
    return time.time()


def make_cbom_cache_key(cbom_data: dict[str, Any]) -> str:
    try:
        payload = json.dumps(cbom_data, sort_keys=True, default=str)
    except TypeError:
        payload = str(cbom_data)
    return f"pqc:{hash(payload)}"


def get_cached_result(key: str) -> dict[str, Any] | None:
    entry = _CACHE.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if _now() >= expires_at:
        _CACHE.pop(key, None)
        return None
    return value


def set_cached_result(key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
    ttl = ttl_seconds or _DEFAULT_TTL_SECONDS
    _CACHE[key] = (_now() + ttl, value)
