from app.core import health


def test_s3_check_requires_bucket_name(monkeypatch):
    monkeypatch.setattr(health.settings.health, "s3_endpoint_url", "https://s3.amazonaws.com")
    monkeypatch.setattr(health.settings.health, "s3_bucket_name", None)

    result = health._s3_check()

    assert result.name == "s3"
    assert result.status == "failed"
    assert result.message == "S3 bucket name is not configured."


def test_run_readiness_checks_uses_client_checks(monkeypatch):
    monkeypatch.setattr(health, "check_db_connection", lambda: True)
    monkeypatch.setattr(health.settings.health, "enable_redis_check", True)
    monkeypatch.setattr(health.settings.health, "enable_s3_check", True)
    monkeypatch.setattr(health.settings.health, "enable_queue_check", True)
    monkeypatch.setattr(
        health,
        "_redis_check",
        lambda: health.CheckResult(name="redis", status="ok"),
    )
    monkeypatch.setattr(
        health,
        "_s3_check",
        lambda: health.CheckResult(name="s3", status="ok"),
    )
    monkeypatch.setattr(
        health,
        "_queue_check",
        lambda: health.CheckResult(name="queue", status="failed", message="queue down"),
    )

    result = health.run_readiness_checks()

    checks = {check.name: check for check in result.checks}
    assert result.status == "degraded"
    assert checks["database"].status == "ok"
    assert checks["redis"].status == "ok"
    assert checks["s3"].status == "ok"
    assert checks["queue"].status == "failed"
