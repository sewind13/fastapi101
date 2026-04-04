from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str


class DependencyCheckResponse(BaseModel):
    name: str
    status: str
    message: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    checks: list[DependencyCheckResponse]


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    path: str
    request_id: str
    details: list[dict] | None = None
