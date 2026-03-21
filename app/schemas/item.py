from app.core.deps import get_current_user # นำเข้าด่านตรวจ
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime # เพิ่มเพื่อรองรับการแสดงเวลา

class ItemBase(BaseModel):
    # ปรับ max_length ให้สอดคล้องกับ Model (255) หรือตาม Business Logic
    title: str = Field(..., examples=["Modern FastAPI"], min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class ItemCreate(ItemBase):
    # ในระดับ Production บางครั้งเราอาจจะอยากรับ owner_id ตรงนี้ 
    # หรือจะดึงจาก Token (JWT) ในตัว API ก็ได้ (แนะนำดึงจาก Token จะปลอดภัยกว่า)
    pass 

class ItemPublic(ItemBase):
    id: int
    owner_id: int
    created_at: datetime # เพิ่มเพื่อให้ Frontend รู้ว่าสร้างเมื่อไหร่

    model_config = ConfigDict(from_attributes=True)