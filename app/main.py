from fastapi import FastAPI
from app.api.v1 import items, users
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# กลุ่มที่ 1: Items
app.include_router(
    items.router, 
    prefix=f"{settings.API_V1_STR}/items", 
    tags=["Items Management"] # ชื่อกลุ่มที่จะโชว์ใน Swagger
)

# กลุ่มที่ 2: Users (กลุ่มใหม่ที่เพิ่มมา)
app.include_router(
    users.router, 
    prefix=f"{settings.API_V1_STR}/users", 
    tags=["User Operations"] # ชื่อกลุ่มที่จะโชว์ใน Swagger
)

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}