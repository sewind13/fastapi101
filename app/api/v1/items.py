from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.item import Item
from app.schemas.item import ItemPublic
from app.schemas.item import ItemCreate
from typing import List

from app.models.user import User as UserModel
from app.core.exception import ItemNotFoundError

from app.core.deps import get_current_user # นำเข้าด่านตรวจ

router = APIRouter()


@router.post("/", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(
    item_in: ItemCreate, 
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user)):

    try:
        # สร้าง Item โดยระบุ owner_id เป็น id ของคนรันคำสั่ง
        db_item = Item.model_validate(item_in, update={"owner_id": current_user.id})
        
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

    if not items:
        # ใช้ Custom Error ของเรา
        raise ItemNotFoundError()

    return items

@router.get("/me", response_model=List[ItemPublic])
def read_my_items(
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
    # เพิ่ม Parameter สำหรับรับค่าจาก URL (Query Parameters)
    offset: int = 0,    # เริ่มดึงจากลำดับที่เท่าไหร่ (เริ่มต้นที่ 0)
    limit: int = Query(default=100, le=100) # ดึงทีละกี่ชิ้น (ค่าเริ่มต้น 100, สูงสุดไม่เกิน 100)
):
    """
    ดึงรายการ Item ของฉัน พร้อมระบบแบ่งหน้า (Pagination)
    """
    # 1. สร้าง Statement พร้อมเงื่อนไขกรองเจ้าของ
    statement = select(Item).where(Item.owner_id == current_user.id)
    
    # 2. ใส่ความสามารถในการข้าม (offset) และจำกัดจำนวน (limit)
    statement = statement.offset(offset).limit(limit)
    
    # 3. รัน Query และดึงผลลัพธ์
    items = session.exec(statement).all()
    
    return items

@router.get("/me-fast", response_model=List[ItemPublic])
def read_my_items_relationship(
    *,
    current_user: UserModel = Depends(get_current_user),
    offset: int = 0,
    limit: int = Query(default=10, le=100) # ตั้ง default เล็กๆ ไว้ก่อน
):
    """
    ดึงรายการ Item ผ่าน Relationship พร้อมระบบแบ่งหน้า (Python Slicing)
    """
    # current_user.items จะคืนค่าเป็น List ของ Item ทั้งหมด
    # เราใช้ Python Slicing [start:end] เพื่อเลือกเฉพาะช่วงที่ต้องการ
    items_slice = current_user.items[offset : offset + limit]
    
    return items_slice