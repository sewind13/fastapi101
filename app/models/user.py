from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
from typing import Optional, List

class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # ตั้งค่า unique=True เพื่อป้องกัน Username หรือ Email ซ้ำในระดับ DB
    username: str = Field(index=True, unique=True, max_length=20)
    email: EmailStr = Field(index=True, unique=True)
    
    # เราจะเก็บผลลัพธ์จากการ Hash เท่านั้น
    hashed_password: str 

    phone: Optional[str] = Field(default=None)
    
    is_active: bool = Field(default=True)

    items: List["Item"] = Relationship(back_populates="owner")