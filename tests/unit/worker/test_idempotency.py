from app.worker.idempotency import InMemoryWorkerIdempotencyStore


def test_in_memory_idempotency_store_tracks_lifecycle():
    store = InMemoryWorkerIdempotencyStore()

    assert store.start("task-1") is True
    assert store.start("task-1") is False
    assert store.is_completed("task-1") is False

    store.complete("task-1")
    assert store.is_completed("task-1") is True

    store.release("task-1")
    assert store.is_completed("task-1") is False
    assert store.start("task-1") is True
