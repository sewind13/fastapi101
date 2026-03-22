from logging.config import fileConfig
import sqlalchemy
from sqlalchemy import engine_from_config, pool
from alembic import context

# --- นำเข้าส่วนประกอบของแอปเรา ---
from sqlmodel import SQLModel
from app.core.config import settings
# สำคัญ: ต้อง Import ทุก Model เข้ามาเพื่อให้ Alembic "เห็น" ตาราง
from app.models.user import User
from app.models.item import Item
# ------------------------------

config = context.config

# ตั้งค่า URL จากไฟล์ .env ของเราเข้าไปในระบบ Alembic
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ระบุ Metadata ของ SQLModel ให้ Alembic ใช้ตรวจสอบความต่าง
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """โหมด Offline: สร้าง SQL Script ออกมาโดยไม่ต่อ DB จริง"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """โหมด Online: เชื่อมต่อและแก้ไขฐานข้อมูล (Neon) จริงๆ"""
    
    # ดึงการตั้งค่าจาก config มาสร้าง engine
    configuration = config.get_section(config.config_ini_section)
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()