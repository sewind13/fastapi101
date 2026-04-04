import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any

from app.core.config import settings
from app.core.metrics import observe_cache_operation


@dataclass
class CacheEntry:
    value: str
    expires_at: datetime


class MemoryCacheBackend:
    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def get(self, key: str) -> str | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.expires_at <= datetime.now(UTC):
                self._store.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        with self._lock:
            self._store[key] = CacheEntry(
                value=value,
                expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
            )

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def delete_prefix(self, prefix: str) -> None:
        with self._lock:
            matching_keys = [key for key in self._store if key.startswith(prefix)]
            for key in matching_keys:
                self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


class RedisCacheBackend:
    def __init__(self) -> None:
        self._client: Any = None
        self._client_url: str | None = None

    def _get_client(self):
        if not settings.cache.redis_url:
            raise RuntimeError("CACHE__REDIS_URL is not configured.")
        if self._client is not None and self._client_url == settings.cache.redis_url:
            return self._client

        from redis import Redis

        self._client = Redis.from_url(
            settings.cache.redis_url,
            decode_responses=True,
        )
        self._client_url = settings.cache.redis_url
        return self._client

    def get(self, key: str) -> str | None:
        value = self._get_client().get(key)
        if value is None:
            return None
        return str(value)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._get_client().set(name=key, value=value, ex=ttl_seconds)

    def delete(self, key: str) -> None:
        self._get_client().delete(key)

    def delete_prefix(self, prefix: str) -> None:
        client = self._get_client()
        keys = list(client.scan_iter(match=f"{prefix}*"))
        if keys:
            client.delete(*keys)


memory_cache = MemoryCacheBackend()
redis_cache = RedisCacheBackend()


def cache_backend():
    if settings.cache.backend == "redis":
        return redis_cache
    return memory_cache


def _build_key(key: str) -> str:
    return f"{settings.cache.key_prefix}:{key}"


def _backend_name() -> str:
    return settings.cache.backend


def get_json(key: str, *, cache_name: str = "default") -> Any | None:
    if not settings.cache.enabled:
        return None
    raw = cache_backend().get(_build_key(key))
    if raw is None:
        observe_cache_operation(
            cache_name=cache_name,
            backend=_backend_name(),
            operation="get",
            outcome="miss",
        )
        return None
    observe_cache_operation(
        cache_name=cache_name,
        backend=_backend_name(),
        operation="get",
        outcome="hit",
    )
    return json.loads(raw)


def set_json(
    key: str,
    value: Any,
    *,
    ttl_seconds: int | None = None,
    cache_name: str = "default",
) -> None:
    if not settings.cache.enabled:
        return
    cache_backend().set(
        _build_key(key),
        json.dumps(value),
        ttl_seconds or settings.cache.default_ttl_seconds,
    )
    observe_cache_operation(
        cache_name=cache_name,
        backend=_backend_name(),
        operation="set",
        outcome="stored",
    )


def delete_key(key: str, *, cache_name: str = "default") -> None:
    if not settings.cache.enabled:
        return
    cache_backend().delete(_build_key(key))
    observe_cache_operation(
        cache_name=cache_name,
        backend=_backend_name(),
        operation="delete",
        outcome="deleted",
    )


def delete_prefix(prefix: str, *, cache_name: str = "default") -> None:
    if not settings.cache.enabled:
        return
    cache_backend().delete_prefix(_build_key(prefix))
    observe_cache_operation(
        cache_name=cache_name,
        backend=_backend_name(),
        operation="delete_prefix",
        outcome="deleted",
    )


def cached_json[T](
    key: str,
    *,
    cache_name: str,
    loader: Callable[[], T],
    serializer: Callable[[T], Any],
    deserializer: Callable[[Any], T],
    ttl_seconds: int | None = None,
) -> T:
    cached_value = get_json(key, cache_name=cache_name)
    if cached_value is not None:
        return deserializer(cached_value)

    loaded_value = loader()
    set_json(
        key,
        serializer(loaded_value),
        ttl_seconds=ttl_seconds,
        cache_name=cache_name,
    )
    return loaded_value
