## 1. Add dependency
- `uv add fastapi --extra standard`
- `uv add fastapi pydantic-settings "uvicorn[standard]"`
- `uv add "pydantic[email]"`
- `uv add "passlib[bcrypt]"`

## 2. Core Concepts
- Use Pydantic to specify schema and process data validation.
- Path and Query parameters (Recieve data from URL).
- Dependency Injection (DI) make code clearner.

## 3. Run FastAPI
- `uv run uvicorn app.main:app --reload`

## 4. Production structure
```
project_root/
├── app/
│   ├── main.py          # จุดเริ่มต้นแอป
│   ├── api/             # เก็บ Routes แยกตามโมดูล
│   ├── core/            # Config, Security, Settings
│   ├── models/          # Database Models (SQLAlchemy/SQLModel)
│   ├── schemas/         # Pydantic Models
│   └── services/        # Business Logic
├── tests/               # การทำ Unit/Integration Test
├── pyproject.toml       # จัดการโดย uv
└── Dockerfile           # สำหรับ Deployment
```

## 5. Test
- Add dependency `uv add --dev pytest pytest-asyncio httpx`
- Add dependency `uv add pytest-cov`
- Directory structure
```
├── app/
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # เก็บ Shared Fixtures (เช่น การตั้งค่า Client)
│   └── test_items.py    # ไฟล์ทดสอบ Logic ของ Items
└── pyproject.toml
```
- Create file `pytest.ini` in the same directory with `pyproject.toml` and put text below.
```
# pytest.ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```
- Run test `uv run pytest`
- Run coverage `uv run pytest --cov=app`

# 6. Change to use real database
- Add dependency `uv add sqlmodel`

# 7. Login JWT
- Add dependency `uv add pyjwt`

# 8. Move to Postguest (Neon)
- Add dependency `uv add "psycopg[binary]"`

# 9. Database Migrations with Alembic
- Add dependency `uv add alembic`
- Create basic config `uv run alembic init alembic`
  - It will create folder `alembic` and file `alembic.ini`
- Setup the file `alembic/env.py`
- Create revision `uv run alembic revision --autogenerate -m "Initial migration"`
  - It will create a file under directory `alembic/versions`
- If we add new field
  - Update `alembic revision --autogenerate -m "add phone field to user"`
  - It will create a file under directory `alembic/versions`
  - Run the update `uv run alembic upgrade head`
  - Database will have new field
  - After that we have to update schema file manually

# 10 .sh command
- Create file `.sh`
- Give permission to run a file `chmod +x run.sh`
- Run script `./run.sh` 