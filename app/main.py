from fastapi import FastAPI, Request
from app.api.v1 import items, users, auth
from app.core.config import settings
from app.core.db import engine

from sqlmodel import SQLModel
from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware # Specify which domain can retrieve data
from fastapi.middleware.gzip import GZipMiddleware # Compress data before sending (faster response and save bandwidth)


# Lifespan to manager database when start/stop
@asynccontextmanager
async def lifespan(app: FastAPI):
    # สร้าง Table ทั้งหมด (เฉพาะช่วง Development ถ้า Production จะใช้ Alembic)
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set Middlewares (Gzip and Cors)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourfrontend.com"], # Allowed domain
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])

# -- Set Routers --
# Group 1: Items
app.include_router(
    items.router, 
    prefix=f"{settings.API_V1_STR}/items", 
    tags=["Items Management"] # Group name on the swagger
)

# Group 2: Users 
app.include_router(
    users.router, 
    prefix=f"{settings.API_V1_STR}/users", 
    tags=["User Operations"] # Group name on the swagger
)

# -- Health Check Endpoints -- (Optional)
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

# -- Global Exception Handler --
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # ในระดับ Production เราควรใช้ Logger เพื่อเก็บ Traceback จริงไว้ดูหลังบ้าน
    # print(f"Error: {exc}") 
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error. Please contact admin."},
    )