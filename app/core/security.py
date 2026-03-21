import bcrypt

import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

def get_password_hash(password: str) -> str:
    # 1. แปลงรหัสผ่านเป็น bytes
    password_bytes = password.encode('utf-8')
    # 2. สร้าง Salt และ Hash
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    # 3. แปลงกลับเป็น string เพื่อเก็บลง Database
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # เทียบรหัสผ่านตัวจริงกับตัวที่ Hash ไว้ใน DB
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt