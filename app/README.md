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