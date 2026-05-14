"""Production ASGI entrypoint.

Application assembly lives in ``app.factory`` so tests and scripts can build
fresh app instances without importing this module-level singleton. Runtime
servers should continue to target ``app.main:app``.
"""

from fastapi import FastAPI

from app.factory import create_app

app: FastAPI = create_app()

__all__ = ["app"]
