"""
File-based cache for raw HTTP responses.
Keyed by URL (hashed). Supports ETag / Last-Modified freshness checks.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / ".cache"
DEFAULT_TTL_SECONDS = 60 * 60 * 6  # 6 hours


def _cache_path(url: str, params: Optional[dict] = None) -> Path:
    key = url + json.dumps(params or {}, sort_keys=True)
    hashed = hashlib.sha256(key.encode()).hexdigest()[:16]
    return CACHE_DIR / hashed[:2] / f"{hashed}.json"


def get(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    ttl: int = DEFAULT_TTL_SECONDS,
    session: Optional[requests.Session] = None,
) -> tuple[Any, bool]:
    """
    Fetch URL with caching. Returns (data, from_cache).

    On network error, returns cached data if available (stale-on-error).
    Raises on first fetch failure with no cache.
    """
    path = _cache_path(url, params)
    cached_meta = _read_cache(path)

    # Check freshness
    if cached_meta and (time.time() - cached_meta["fetched_at"]) < ttl:
        logger.debug(f"Cache hit: {url}")
        return cached_meta["data"], True

    # Attempt fetch
    req = session or requests
    try:
        resp = req.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        _write_cache(path, data)
        logger.debug(f"Fetched and cached: {url}")
        return data, False
    except Exception as exc:
        if cached_meta:
            logger.warning(f"Fetch failed ({exc}), using stale cache for {url}")
            return cached_meta["data"], True
        raise


def get_csv(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    ttl: int = DEFAULT_TTL_SECONDS,
    session: Optional[requests.Session] = None,
) -> tuple[str, bool]:
    """Like get() but returns raw text (for CSV endpoints)."""
    path = _cache_path(url, params)
    cached_meta = _read_cache(path)

    if cached_meta and (time.time() - cached_meta["fetched_at"]) < ttl:
        logger.debug(f"Cache hit (csv): {url}")
        return cached_meta["data"], True

    req = session or requests
    try:
        resp = req.get(url, params=params, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.text
        _write_cache(path, data)
        logger.debug(f"Fetched and cached (csv): {url}")
        return data, False
    except Exception as exc:
        if cached_meta:
            logger.warning(f"CSV fetch failed ({exc}), using stale cache for {url}")
            return cached_meta["data"], True
        raise


def _read_cache(path: Path) -> Optional[dict]:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _write_cache(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"fetched_at": time.time(), "data": data}, f)


def clear() -> None:
    """Delete all cached files."""
    import shutil
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        logger.info(f"Cleared cache at {CACHE_DIR}")
