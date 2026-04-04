from dataclasses import dataclass


@dataclass(slots=True)
class ServiceError:
    code: str
    message: str


@dataclass(slots=True)
class ServiceResult[T]:
    value: T | None = None
    error: ServiceError | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class BaseService:
    def success[T](self, value: T) -> ServiceResult[T]:
        return ServiceResult(value=value)

    def failure[T](self, code: str, message: str) -> ServiceResult[T]:
        return ServiceResult(error=ServiceError(code=code, message=message))
