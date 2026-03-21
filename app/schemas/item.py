from pydantic import BaseModel, Field

# In product grade we have to separate schemes for create and read

class ItemBase(BaseModel):
    title: str = Field(..., example="Modern FastAPI")
    description: str | None = None

class ItemCreate(ItemBase):
    pass  # ข้อมูลที่รับจาก Client ตอนสร้าง

class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True # รองรับการแปลงจาก ORM (เช่น SQLAlchemy)