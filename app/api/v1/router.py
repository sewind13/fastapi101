from fastapi import APIRouter

from app.api.v1 import auth, billing, items, ops, users
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(users.router, prefix="/users", tags=["User Operations"])
api_router.include_router(ops.router, prefix="/ops", tags=["Operations"])

if settings.examples.enable_items_module:
    api_router.include_router(items.router, prefix="/items", tags=["Example Items"])
