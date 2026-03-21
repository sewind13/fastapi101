from fastapi import APIRouter, HTTPException, status
from app.schemas.item import Item, ItemCreate

router = APIRouter()

fake_db = []

@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item_in: ItemCreate):
    """
    สร้าง Item ใหม่พร้อม Metadata สำหรับ Document
    """
    new_item = Item(
        id=len(fake_db) + 1,
        owner_id=1,
        **item_in.model_dump()
    )
    fake_db.append(new_item)
    return new_item

@router.get("/{item_id}", response_model=Item)
async def read_item(item_id: int):
    if item_id > len(fake_db) or item_id < 1:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลที่คุณระบุ")
    return fake_db[item_id - 1]