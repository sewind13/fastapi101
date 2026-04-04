from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import logger


def configure_telemetry(app: FastAPI, engine=None) -> None:
    if not settings.telemetry.enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning("opentelemetry dependencies are not installed")
        return

    resource = Resource.create(
        {
            "service.name": settings.telemetry.service_name,
            "service.version": settings.telemetry.service_version,
        }
    )
    provider = TracerProvider(resource=resource)

    if settings.telemetry.exporter_otlp_endpoint:
        span_exporter = OTLPSpanExporter(
            endpoint=settings.telemetry.exporter_otlp_endpoint,
            insecure=settings.telemetry.exporter_otlp_insecure,
        )
    else:
        span_exporter = OTLPSpanExporter(
            insecure=settings.telemetry.exporter_otlp_insecure,
        )
    provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    if engine is not None:
        instrumented_engine = engine.sync_engine if hasattr(engine, "sync_engine") else engine
        SQLAlchemyInstrumentor().instrument(engine=instrumented_engine)
