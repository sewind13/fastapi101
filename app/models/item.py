from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Item(SQLModel, table=True):
    # เพิ่มบรรทัดนี้เพื่อแก้ปัญหา Table 'item' is already defined
    __table_args__ = {"extend_existing": True} 

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, max_length=255)
    description: Optional[str] = None

    # ForeignKey: เชื่อมไปยังตาราง User (สมมติว่าตารางชื่อ user)
    owner_id: int = Field(foreign_key="user.id", index=True)

    # Timestamp: ช่วยในการทำ Audit และ Sorting ข้อมูลในอนาคต
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Optional: ถ้าต้องการดึงข้อมูล User ออกมาพร้อม Item ได้ง่ายๆ
    # owner: Optional["User"] = Relationship(back_populates="items")

