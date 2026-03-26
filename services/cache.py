"""
Lightweight in-memory TTL cache.
Usage:
    from services.cache import TTLCache
    _alias_cache = TTLCache(ttl=300)   # 5 min
    _alias_cache.set("alice", "SwiftFox#1234")
    _alias_cache.get("alice")          # -> "SwiftFox#1234" or None if expired
    _alias_cache.delete("alice")       # invalidate on update
"""
import time
from typing import Any, Optional


class TTLCache:
    def __init__(self, ttl: float = 60.0):
        self._ttl   = ttl
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self._store[key] = (value, time.monotonic() + (ttl if ttl is not None else self._ttl))

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
