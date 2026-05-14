from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.health import run_readiness_checks
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")


@router.get("/health/live", response_model=HealthResponse)
async def liveness_check():
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check():
    readiness = run_readiness_checks()
    if readiness.status != "ok":
        return JSONResponse(
            status_code=503,
            content=readiness.model_dump(),
        )
    return readiness
