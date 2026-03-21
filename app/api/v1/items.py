from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.item import Item
from app.schemas.item import ItemPublic
from app.schemas.item import ItemCreate

from app.models.user import User as UserModel

from app.core.deps import get_current_user # นำเข้าด่านตรวจ

router = APIRouter()


@router.post("/", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(
    item_in: ItemCreate, 
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user)):

    try:
        # แปลง Pydantic เป็น SQLModel
        db_item = Item(**item_in.model_dump(), owner_id=current_user.id)
        
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
    current_user: UserModel = Depends(get_current_user),
    limit: int = Query(default=100, le=500), # เพิ่ม Pagination เพื่อรองรับข้อมูลจำนวนมาก
    offset: int = 0
):
    # ดึงเฉพาะ Item "ที่เป็นของคน Login เท่านั้น" (Privacy)
    statement = select(Item).where(Item.owner_id == current_user.id).offset(offset).limit(limit)
    items = session.exec(statement).all()
    return items
