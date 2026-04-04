from app.core.metrics import render_metrics
from app.jobs import cleanup_revoked_tokens as cleanup_job
from app.services.result import ServiceResult


def test_cleanup_job_emits_maintenance_metrics(monkeypatch):
    class DummySession:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(cleanup_job, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(cleanup_job, "configure_logging", lambda: None)
    monkeypatch.setattr(
        cleanup_job,
        "cleanup_revoked_tokens",
        lambda session: ServiceResult(value=3),
    )

    exit_code = cleanup_job.main()

    payload, _ = render_metrics()
    body = payload.decode()

    assert exit_code == 0
    assert "fastapi_template_maintenance_job_runs_total" in body
    assert 'job_name="cleanup_revoked_tokens",outcome="succeeded"' in body
    assert "fastapi_template_maintenance_job_deleted_total" in body
