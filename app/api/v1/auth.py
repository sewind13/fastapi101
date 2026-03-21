from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.core.db import get_session
from app.core.security import verify_password, create_access_token
from app.models.user import User as UserModel
from app.schemas.token import Token

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    # OAuth2PasswordRequestForm จะรับ username และ password มาให้โดยอัตโนมัติ
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    # 1. ค้นหา User จาก Username
    user = session.exec(select(UserModel).where(UserModel.username == form_data.username)).first()
    
    # 2. ตรวจสอบ User และ Password (ใช้ verify_password ที่เราเขียนไว้)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username หรือ Password ไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. สร้าง Token โดยใช้ ID หรือ Username
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}