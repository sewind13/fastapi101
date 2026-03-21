import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import get_session
from app.models.user import User as UserModel

# บอก FastAPI ว่าจะหา Token ได้จาก URL ไหน (ใช้สำหรับปุ่ม Authorize ใน Swagger)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    session: Session = Depends(get_session), 
    token: str = Depends(oauth2_scheme)
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="ไม่สามารถยืนยันตัวตนได้",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. ถอดรหัส Token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # 2. ค้นหา User ใน Database จาก Username ที่อยู่ใน Token
    user = session.exec(select(UserModel).where(UserModel.username == username)).first()
    if user is None:
        raise credentials_exception
    
    return user