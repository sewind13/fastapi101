## 1. Add dependency
- `uv add fastapi --extra standard`
- `uv add fastapi pydantic-settings "uvicorn[standard]"`
- `uv add "pydantic[email]"`

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