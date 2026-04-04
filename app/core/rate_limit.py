from collections import defaultdict, deque
from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from threading import Lock
from time import monotonic
from typing import Protocol

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import TooManyRequestsException
from app.services.exceptions import ErrorCode


@dataclass(slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class RateLimitBackend(Protocol):
    def check(self, *, key: str, max_attempts: int, window_seconds: int) -> RateLimitDecision: ...
    def hit(self, *, key: str, max_attempts: int, window_seconds: int) -> RateLimitDecision: ...
    def reset(self, *, key: str) -> None: ...
    def clear(self) -> None: ...


class InMemoryFixedWindowRateLimiter:
    def __init__(self):
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, now: float, window_seconds: int) -> deque[float]:
        attempts = self._attempts[key]
        cutoff = now - window_seconds
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        if not attempts:
            self._attempts.pop(key, None)
        return attempts

    def check(self, *, key: str, max_attempts: int, window_seconds: int) -> RateLimitDecision:
        now = monotonic()
        with self._lock:
            attempts = self._prune(key, now, window_seconds)
            if len(attempts) >= max_attempts:
                retry_after = max(1, int(window_seconds - (now - attempts[0])))
                return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)
        return RateLimitDecision(allowed=True, retry_after_seconds=0)

    def hit(self, *, key: str, max_attempts: int, window_seconds: int) -> RateLimitDecision:
        now = monotonic()
        with self._lock:
            attempts = self._prune(key, now, window_seconds)
            attempts.append(now)
            self._attempts[key] = attempts
            if len(attempts) >= max_attempts:
                retry_after = max(1, int(window_seconds - (now - attempts[0])))
                return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)
        return RateLimitDecision(allowed=True, retry_after_seconds=0)

    def reset(self, *, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._attempts.clear()


class RedisFixedWindowRateLimiter:
    def __init__(self):
        self._client = None
        self._client_url: str | None = None

    def _get_client(self):
        if not settings.auth_rate_limit.redis_url:
            raise RuntimeError("AUTH_RATE_LIMIT__REDIS_URL is not configured.")

        if self._client is not None and self._client_url == settings.auth_rate_limit.redis_url:
            return self._client

        from redis import Redis

        self._client = Redis.from_url(
            settings.auth_rate_limit.redis_url,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
        self._client_url = settings.auth_rate_limit.redis_url
        return self._client

    def check(self, *, key: str, max_attempts: int, window_seconds: int) -> RateLimitDecision:
        client = self._get_client()
        raw_count = client.get(key)
        count = int(raw_count) if raw_count is not None else 0
        if count >= max_attempts:
            ttl = client.ttl(key)
            retry_after = ttl if ttl and ttl > 0 else window_seconds
            return RateLimitDecision(allowed=False, retry_after_seconds=int(retry_after))
        return RateLimitDecision(allowed=True, retry_after_seconds=0)

    def hit(self, *, key: str, max_attempts: int, window_seconds: int) -> RateLimitDecision:
        client = self._get_client()
        pipeline = client.pipeline()
        pipeline.incr(key)
        pipeline.ttl(key)
        count, ttl = pipeline.execute()

        if int(count) == 1 or int(ttl) < 0:
            client.expire(key, window_seconds)
            ttl = window_seconds

        if int(count) >= max_attempts:
            retry_after = int(ttl) if int(ttl) > 0 else window_seconds
            return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)
        return RateLimitDecision(allowed=True, retry_after_seconds=0)

    def reset(self, *, key: str) -> None:
        client = self._get_client()
        client.delete(key)

    def clear(self) -> None:
        client = self._get_client()
        prefix = f"{settings.auth_rate_limit.key_prefix}:*"
        keys = list(client.scan_iter(match=prefix))
        if keys:
            client.delete(*keys)


memory_rate_limiter = InMemoryFixedWindowRateLimiter()
redis_rate_limiter = RedisFixedWindowRateLimiter()
login_rate_limiter = memory_rate_limiter
token_rate_limiter = memory_rate_limiter


def _backend() -> RateLimitBackend:
    if settings.auth_rate_limit.backend == "redis":
        return redis_rate_limiter
    return memory_rate_limiter


def _is_trusted_proxy(ip: str | None) -> bool:
    if not ip:
        return False
    try:
        parsed_ip = ip_address(ip)
    except ValueError:
        return False

    for cidr in settings.auth_rate_limit.trusted_proxy_cidrs:
        if cidr == "*":
            return True
        try:
            if parsed_ip in ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def _extract_forwarded_ip(request: Request) -> str | None:
    x_forwarded_for = request.headers.get("x-forwarded-for", "")
    if x_forwarded_for:
        for part in x_forwarded_for.split(","):
            candidate = part.strip()
            if candidate:
                return candidate

    x_real_ip = request.headers.get("x-real-ip", "").strip()
    if x_real_ip:
        return x_real_ip

    return None


def _client_ip(request: Request) -> str:
    direct_ip = request.client.host if request.client and request.client.host else None
    if not settings.auth_rate_limit.trust_proxy_headers:
        return direct_ip or "unknown"

    if not _is_trusted_proxy(direct_ip):
        return direct_ip or "unknown"

    forwarded_ip = _extract_forwarded_ip(request)
    if forwarded_ip:
        return forwarded_ip
    return direct_ip or "unknown"


def _key(*parts: str) -> str:
    prefix = settings.auth_rate_limit.key_prefix.strip(":")
    normalized = [part.strip().lower() for part in parts if part.strip()]
    return ":".join([prefix, *normalized])


def login_rate_limit_key(request: Request, username: str) -> str:
    return _key("login", _client_ip(request), username)


def token_rate_limit_key(request: Request, endpoint: str) -> str:
    return _key(endpoint, _client_ip(request))


def _rate_limit_exception(message: str, retry_after_seconds: int) -> TooManyRequestsException:
    return TooManyRequestsException(
        message=message,
        error_code=ErrorCode.AUTH_RATE_LIMITED,
        retry_after_seconds=retry_after_seconds,
    )


def check_login_rate_limit(request: Request, username: str) -> TooManyRequestsException | None:
    if not settings.auth_rate_limit.enabled:
        return None

    decision = _backend().check(
        key=login_rate_limit_key(request, username),
        max_attempts=settings.auth_rate_limit.login_max_attempts,
        window_seconds=settings.auth_rate_limit.login_window_seconds,
    )
    if decision.allowed:
        return None

    return _rate_limit_exception(
        "Too many failed login attempts. Please try again later.",
        decision.retry_after_seconds,
    )


def record_login_attempt(
    request: Request, username: str, *, success: bool
) -> TooManyRequestsException | None:
    if not settings.auth_rate_limit.enabled:
        return None

    key = login_rate_limit_key(request, username)
    backend = _backend()
    if success:
        backend.reset(key=key)
        return None

    decision = backend.hit(
        key=key,
        max_attempts=settings.auth_rate_limit.login_max_attempts,
        window_seconds=settings.auth_rate_limit.login_window_seconds,
    )
    if decision.allowed:
        return None

    return _rate_limit_exception(
        "Too many failed login attempts. Please try again later.",
        decision.retry_after_seconds,
    )


def check_token_rate_limit(request: Request, endpoint: str) -> TooManyRequestsException | None:
    if not settings.auth_rate_limit.enabled:
        return None

    decision = _backend().hit(
        key=token_rate_limit_key(request, endpoint),
        max_attempts=settings.auth_rate_limit.token_max_attempts,
        window_seconds=settings.auth_rate_limit.token_window_seconds,
    )
    if decision.allowed:
        return None

    return _rate_limit_exception(
        "Too many authentication requests. Please try again later.",
        decision.retry_after_seconds,
    )
