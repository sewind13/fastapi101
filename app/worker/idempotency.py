from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Protocol

from app.core.config import settings


class WorkerIdempotencyBackend(Protocol):
    def start(self, task_id: str) -> bool: ...
    def complete(self, task_id: str) -> None: ...
    def release(self, task_id: str) -> None: ...
    def is_completed(self, task_id: str) -> bool: ...
    def clear(self) -> None: ...


@dataclass
class _StateRecord:
    state: str
    expires_at: float


class InMemoryWorkerIdempotencyStore:
    def __init__(self):
        self._records: dict[str, _StateRecord] = {}
        self._lock = Lock()

    def _prune(self) -> None:
        now = time()
        expired = [key for key, record in self._records.items() if record.expires_at <= now]
        for key in expired:
            self._records.pop(key, None)

    def start(self, task_id: str) -> bool:
        with self._lock:
            self._prune()
            record = self._records.get(task_id)
            if record is not None:
                return False
            self._records[task_id] = _StateRecord(
                state="processing",
                expires_at=time() + settings.worker.idempotency_ttl_seconds,
            )
            return True

    def complete(self, task_id: str) -> None:
        with self._lock:
            self._records[task_id] = _StateRecord(
                state="completed",
                expires_at=time() + settings.worker.idempotency_ttl_seconds,
            )

    def release(self, task_id: str) -> None:
        with self._lock:
            self._records.pop(task_id, None)

    def is_completed(self, task_id: str) -> bool:
        with self._lock:
            self._prune()
            record = self._records.get(task_id)
            return record is not None and record.state == "completed"

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


class RedisWorkerIdempotencyStore:
    def __init__(self):
        self._client = None
        self._client_url: str | None = None

    def _get_client(self):
        if not settings.worker.idempotency_redis_url:
            raise RuntimeError("WORKER__IDEMPOTENCY_REDIS_URL is not configured.")

        if self._client is not None and self._client_url == settings.worker.idempotency_redis_url:
            return self._client

        from redis import Redis

        self._client = Redis.from_url(
            settings.worker.idempotency_redis_url,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
        self._client_url = settings.worker.idempotency_redis_url
        return self._client

    def _key(self, task_id: str) -> str:
        return f"{settings.worker.idempotency_key_prefix}:{task_id}"

    def start(self, task_id: str) -> bool:
        client = self._get_client()
        return bool(
            client.set(
                self._key(task_id),
                "processing",
                nx=True,
                ex=settings.worker.idempotency_ttl_seconds,
            )
        )

    def complete(self, task_id: str) -> None:
        client = self._get_client()
        client.set(
            self._key(task_id),
            "completed",
            ex=settings.worker.idempotency_ttl_seconds,
        )

    def release(self, task_id: str) -> None:
        client = self._get_client()
        client.delete(self._key(task_id))

    def is_completed(self, task_id: str) -> bool:
        client = self._get_client()
        return client.get(self._key(task_id)) == "completed"

    def clear(self) -> None:
        client = self._get_client()
        prefix = f"{settings.worker.idempotency_key_prefix}:*"
        keys = list(client.scan_iter(match=prefix))
        if keys:
            client.delete(*keys)


memory_worker_idempotency = InMemoryWorkerIdempotencyStore()
redis_worker_idempotency = RedisWorkerIdempotencyStore()


def worker_idempotency_backend() -> WorkerIdempotencyBackend:
    if settings.worker.idempotency_backend == "redis":
        return redis_worker_idempotency
    return memory_worker_idempotency
