from app.core import cache


def test_memory_cache_set_get_and_delete_prefix(monkeypatch):
    monkeypatch.setattr(cache.settings.cache, "enabled", True)
    monkeypatch.setattr(cache.settings.cache, "backend", "memory")
    monkeypatch.setattr(cache.settings.cache, "key_prefix", "cache")
    cache.memory_cache.clear()

    cache.set_json("items:owner:1:offset:0:limit:10", [{"id": 1}], ttl_seconds=60)
    cache.set_json("items:owner:1:offset:10:limit:10", [{"id": 2}], ttl_seconds=60)
    cache.set_json("items:owner:2:offset:0:limit:10", [{"id": 3}], ttl_seconds=60)

    assert cache.get_json("items:owner:1:offset:0:limit:10") == [{"id": 1}]
    cache.delete_prefix("items:owner:1:")
    assert cache.get_json("items:owner:1:offset:0:limit:10") is None
    assert cache.get_json("items:owner:1:offset:10:limit:10") is None
    assert cache.get_json("items:owner:2:offset:0:limit:10") == [{"id": 3}]


def test_memory_cache_disabled_returns_none(monkeypatch):
    monkeypatch.setattr(cache.settings.cache, "enabled", False)
    cache.memory_cache.clear()

    cache.set_json("disabled-key", {"ok": True}, ttl_seconds=60)

    assert cache.get_json("disabled-key") is None


def test_cached_json_loads_once_and_then_hits_cache(monkeypatch):
    monkeypatch.setattr(cache.settings.cache, "enabled", True)
    monkeypatch.setattr(cache.settings.cache, "backend", "memory")
    cache.memory_cache.clear()

    calls = {"count": 0}

    def loader():
        calls["count"] += 1
        return [{"id": 1}]

    first = cache.cached_json(
        "items:list",
        cache_name="items_list",
        loader=loader,
        serializer=lambda value: value,
        deserializer=lambda value: value,
        ttl_seconds=60,
    )
    second = cache.cached_json(
        "items:list",
        cache_name="items_list",
        loader=loader,
        serializer=lambda value: value,
        deserializer=lambda value: value,
        ttl_seconds=60,
    )

    assert first == [{"id": 1}]
    assert second == [{"id": 1}]
    assert calls["count"] == 1
