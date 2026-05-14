from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.metrics import render_metrics

router = APIRouter()


if settings.metrics.enabled:

    @router.get(settings.metrics.path, include_in_schema=settings.metrics.include_in_schema)
    async def metrics(request: Request) -> Response:
        if settings.metrics.auth_token:
            authorization = request.headers.get("authorization", "")
            expected = f"Bearer {settings.metrics.auth_token}"
            if authorization != expected:
                raise UnauthorizedException("Metrics authentication failed.")
        payload, content_type = render_metrics()
        return Response(content=payload, media_type=content_type)
