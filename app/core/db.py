from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings

# ใช้ SQLite สำหรับเริ่มต้น (ใน Prod จริงแค่เปลี่ยน URL เป็น PostgreSQL)
sqlite_url = "sqlite:///./database.db"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session