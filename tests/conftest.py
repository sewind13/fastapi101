# tests/conftest.py
import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel, Session, create_engine, StaticPool
from app.main import app
from app.core.db import get_session
from app.core.security import create_access_token

# 1. สร้าง DB จำลองใน Memory
sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(name="session")
def session_fixture():
    # สร้างตารางใหม่ทุกครั้งที่เริ่ม Test
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # ลบทิ้งเมื่อ Test จบ
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
async def client_fixture(session: Session):
    # 2. Override get_session ให้ใช้ DB จำลอง
    def get_session_override():
        yield session
    
    app.dependency_overrides[get_session] = get_session_override
    
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac
    
    # ล้างค่า Override หลังจบ Test
    app.dependency_overrides.clear()

@pytest.fixture
def token_headers(session: Session):
    """Fixture สำหรับสร้าง Token จำลอง เพื่อใช้ใน Test ที่ต้อง Login"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    # สร้าง User จำลองใน DB
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # สร้าง Token
    token = create_access_token(data={"sub": user.username})
    return {"Authorization": f"Bearer {token}"}