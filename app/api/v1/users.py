from fastapi import APIRouter, HTTPException, status
from app.schemas.user import User, UserCreate

router = APIRouter()

# จำลอง Database สำหรับ User
fake_users_db = []

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate):
    # ตรวจสอบว่า Email ซ้ำไหม (Logic จำลอง)
    if any(u.email == user_in.email for u in fake_users_db):
        raise HTTPException(
            status_code=400, 
            detail="อีเมลนี้ถูกใช้งานไปแล้ว"
        )
    
    new_user = User(
        id=len(fake_users_db) + 1,
        **user_in.model_dump(exclude={"password"}) # ไม่ส่ง Password กลับไปใน Response
    )
    fake_users_db.append(new_user)
    return new_user

@router.get("/me", response_model=User)
async def get_current_user():
    # ในอนาคตตรงนี้จะใช้ Dependency Injection ตรวจสอบ Token
    if not fake_users_db:
        raise HTTPException(status_code=404, detail="ยังไม่มีผู้ใช้ในระบบ")
    return fake_users_db[0]