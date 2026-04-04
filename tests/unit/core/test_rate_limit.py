from starlette.requests import Request

from app.core import rate_limit
from app.core.config import settings


class FakePipeline:
    def __init__(self, store: dict[str, int], ttl_store: dict[str, int], key_ref: list[str]):
        self.store = store
        self.ttl_store = ttl_store
        self.key_ref = key_ref

    def incr(self, key: str):
        self.key_ref.append(key)
        self.store[key] = self.store.get(key, 0) + 1
        return self

    def ttl(self, key: str):
        self.key_ref.append(key)
        return self

    def execute(self):
        key = self.key_ref[-1]
        return self.store[key], self.ttl_store.get(key, -1)


class FakeRedisClient:
    def __init__(self):
        self.store: dict[str, int] = {}
        self.ttl_store: dict[str, int] = {}

    def get(self, key: str):
        value = self.store.get(key)
        return str(value) if value is not None else None

    def ttl(self, key: str):
        return self.ttl_store.get(key, -1)

    def pipeline(self):
        return FakePipeline(self.store, self.ttl_store, [])

    def expire(self, key: str, ttl: int):
        self.ttl_store[key] = ttl

    def delete(self, *keys: str):
        for key in keys:
            self.store.pop(key, None)
            self.ttl_store.pop(key, None)

    def scan_iter(self, match: str):
        prefix = match.removesuffix("*")
        for key in list(self.store):
            if key.startswith(prefix):
                yield key


def make_request(ip: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/login",
        "headers": [],
        "client": (ip, 12345),
    }
    return Request(scope)


def test_redis_backend_blocks_after_threshold(monkeypatch):
    fake_client = FakeRedisClient()
    monkeypatch.setattr(settings.auth_rate_limit, "backend", "redis")
    monkeypatch.setattr(settings.auth_rate_limit, "redis_url", "redis://redis:6379/0")
    monkeypatch.setattr(settings.auth_rate_limit, "login_max_attempts", 2)
    monkeypatch.setattr(settings.auth_rate_limit, "login_window_seconds", 300)
    monkeypatch.setattr(rate_limit.redis_rate_limiter, "_client", fake_client)
    monkeypatch.setattr(
        rate_limit.redis_rate_limiter,
        "_client_url",
        settings.auth_rate_limit.redis_url,
    )

    request = make_request()

    first = rate_limit.record_login_attempt(request, "alice", success=False)
    second = rate_limit.record_login_attempt(request, "alice", success=False)
    third = rate_limit.check_login_rate_limit(request, "alice")

    assert first is None
    assert second is not None
    assert second.error_code == "auth.rate_limited"
    assert third is not None
    assert third.error_code == "auth.rate_limited"


def test_successful_login_resets_redis_key(monkeypatch):
    fake_client = FakeRedisClient()
    monkeypatch.setattr(settings.auth_rate_limit, "backend", "redis")
    monkeypatch.setattr(settings.auth_rate_limit, "redis_url", "redis://redis:6379/0")
    monkeypatch.setattr(rate_limit.redis_rate_limiter, "_client", fake_client)
    monkeypatch.setattr(
        rate_limit.redis_rate_limiter,
        "_client_url",
        settings.auth_rate_limit.redis_url,
    )

    request = make_request()
    key = rate_limit.login_rate_limit_key(request, "alice")
    fake_client.store[key] = 3
    fake_client.ttl_store[key] = 120

    result = rate_limit.record_login_attempt(request, "alice", success=True)

    assert result is None
    assert key not in fake_client.store


def test_client_ip_uses_forwarded_header_only_for_trusted_proxy(monkeypatch):
    monkeypatch.setattr(settings.auth_rate_limit, "trust_proxy_headers", True)
    monkeypatch.setattr(settings.auth_rate_limit, "trusted_proxy_cidrs", ["10.0.0.0/8"])

    trusted_scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/login",
        "headers": [(b"x-forwarded-for", b"203.0.113.10, 10.0.0.5")],
        "client": ("10.1.2.3", 12345),
    }
    untrusted_scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/login",
        "headers": [(b"x-forwarded-for", b"203.0.113.10, 10.0.0.5")],
        "client": ("198.51.100.5", 12345),
    }

    trusted_request = Request(trusted_scope)
    untrusted_request = Request(untrusted_scope)

    assert rate_limit.login_rate_limit_key(trusted_request, "alice").startswith(
        "rate_limit:login:203.0.113.10:alice"
    )
    assert rate_limit.login_rate_limit_key(untrusted_request, "alice").startswith(
        "rate_limit:login:198.51.100.5:alice"
    )
