from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from app.core.db import get_session
from app.core.security import get_password_hash
from app.models.user import User as UserModel
from app.schemas.user import UserPublic, UserCreate # ใช้ชื่อใหม่ที่เราคุยกัน

router = APIRouter()

@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, session: Session = Depends(get_session)):
    # 1. ตรวจสอบว่ามี User หรือ Email นี้อยู่แล้วหรือไม่
    query = select(UserModel).where(
        (UserModel.username == user_in.username) | (UserModel.email == user_in.email)
    )
    existing_user = session.exec(query).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username หรือ Email นี้ถูกใช้งานไปแล้ว"
        )

    # 2. ทำการ Hash รหัสผ่านก่อนบันทึก
    hashed_pw = get_password_hash(user_in.password)

    # 3. สร้าง User Object และบันทึก
    db_user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pw
    )
    
    try:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    except Exception:
        session.rollback()
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการสร้างบัญชี")
    
@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(user_id: int, session: Session = Depends(get_session)):
    """
    ดึงข้อมูลผู้ใช้จาก ID
    """
    # 1. ค้นหา User ใน Database
    user = session.get(UserModel, user_id)
    
    # 2. ถ้าไม่เจอ ให้แจ้ง Error 404 ทันที
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ไม่พบผู้ใช้รหัส {user_id} ในระบบ"
        )
    
    # 3. ส่งข้อมูลกลับ (FastAPI จะแปลงเป็น UserPublic ให้อัตโนมัติ)
    return user