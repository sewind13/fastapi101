from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.item import Item
from app.schemas.item import ItemPublic
from app.schemas.item import ItemCreate


router = APIRouter()


@router.post("/", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate, session: Session = Depends(get_session)):
    try:
        # แปลง Pydantic เป็น SQLModel
        db_item = Item(**item_in.model_dump(), owner_id=1)
        
        session.add(db_item)
        session.commit() # จุดที่มักจะเกิด Error
        session.refresh(db_item)
        return db_item
    except Exception as e:
        session.rollback() # ถ้าพังต้อง Rollback ข้อมูลกลับ
        # Log error ไว้ดูหลังบ้าน (Production practice)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ไม่สามารถบันทึกข้อมูลได้ในขณะนี้"
        )

@router.get("/", response_model=list[ItemPublic])
def read_items(
    session: Session = Depends(get_session),
    limit: int = Query(default=100, le=500), # เพิ่ม Pagination เพื่อรองรับข้อมูลจำนวนมาก
    offset: int = 0
):
    # การดึงข้อมูลควรมี limit เสมอเพื่อไม่ให้ Server ค้างถ้ามีข้อมูลหลักแสน
    statement = select(Item).order_by(Item.created_at.desc()).offset(offset).limit(limit)
    items = session.exec(statement).all()
    return items
