from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional  # <--- แยกออกมาไว้ที่นี่

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72, examples=["secret1234"])
    phone: Optional[str] = None # เพิ่มเพื่อให้รับค่าจาก API ได้

class UserPublic(UserBase):
    id: int
    is_active: bool = True
    phone: Optional[str] = None # เพิ่มเพื่อให้รับค่าจาก API ได้

    model_config = ConfigDict(from_attributes=True)
    