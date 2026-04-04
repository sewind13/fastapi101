# การพัฒนาในเครื่อง

ไฟล์นี้สรุป workflow ตอนพัฒนาใน local ตั้งแต่รันระบบ, ดู logs, รัน quality checks, ไปจนถึงการเพิ่ม feature ใหม่

## Local development flow ที่แนะนำ

1. sync dependencies
2. copy `.env`
3. รัน stack
4. bootstrap admin ถ้าจำเป็น
5. พัฒนา feature
6. รัน lint/typecheck/tests ก่อน push

## Setup ครั้งแรก

```bash
uv sync --frozen --all-groups
pre-commit install
cp .env.min.example .env
make up
```

## รันระบบในเครื่อง

คำสั่งหลัก:

```bash
make up
```

สิ่งที่จะได้:

- Postgres
- FastAPI app
- ถ้าเปิด worker profile จะมี queue / worker / outbox-dispatcher เพิ่ม

คำสั่งช่วยดูสถานะ:

```bash
make ps
make logs
make shell-web
make psql-web
```

ถ้ากำลังจะแก้ table หรือ column ให้เปิด [database-migrations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-migrations.md) ประกบไว้ก่อน เพราะไฟล์นั้นอธิบาย flow การแก้ schema และวิธี debug ปัญหา local DB โดยตรง

ถ้าจะปิด:

```bash
make down
```

## ตอนเจอปัญหา local ที่พบบ่อย

### app ต่อ DB ไม่ได้

เช็ก:

- `make ps`
- `make logs`
- `make psql-web`

ถ้ารันคำสั่งจากบนเครื่องตรง ๆ แล้วเจอ host `db` ไม่ได้ ให้จำไว้ว่าชื่อ `db` ใช้ได้จากใน compose network เป็นหลัก

### schema ไม่ตรงกับ code

ให้ลอง:

```bash
make migrate
```

ถ้ายังเพี้ยนและเป็น local DB ที่ไม่มีข้อมูลสำคัญ อาจต้อง reset volume แล้วขึ้นใหม่

## Quality gates

ก่อน push ควรรัน:

```bash
make lint
make format
make typecheck
uv run pytest -q
```

repo นี้มี:

- pre-commit
- GitHub Actions CI
- mypy
- ruff
- pytest

ดังนั้นควรถือว่าคำสั่งเหล่านี้เป็น baseline ในการพัฒนา

## Workflow ตอนเพิ่ม feature ใหม่

pattern หลักของ template นี้คือ:

`route -> service -> repository -> model -> schema -> tests`

หลักคิดคือ:

- route บาง
- service ถือ business logic
- repository คุยกับ DB
- schema เป็น request/response contract

## ตอนจะเพิ่มโมดูลใหม่

ปกติจะต้องแตะไฟล์ประมาณนี้:

- `app/schemas/<feature>.py`
- `app/db/models/<feature>.py`
- `app/db/repositories/<feature>.py`
- `app/services/<feature>_service.py`
- `app/api/v1/<feature>.py`
- `app/api/v1/router.py`
- `alembic/versions/*.py`
- tests ที่เกี่ยวข้อง

ถ้าฟีเจอร์ใหม่มี table หรือ column ใหม่ ควรอ่านคู่กับ:

- [database-schema.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-schema.md)
- [database-migrations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-migrations.md)

## Example ที่ควรดูใน repo นี้

### `items`

ใช้ดู pattern ของ:

- CRUD slice
- service/repository separation
- integration tests
- entitlement/quota enforcement example

### `billing` / `ops`

ใช้ดู pattern ของ:

- wrapper schemas
- filtering/pagination/report endpoints
- role-protected operational routes

## คำสั่งที่เกี่ยวกับ admin bootstrap

ถ้าระบบรันผ่าน compose อยู่ แนะนำให้ใช้:

```bash
export BOOTSTRAP_ADMIN_PASSWORD='replace-with-a-strong-secret'
make bootstrap-admin-in-container-env args="--username admin --email admin@example.com"
```

หรือ:

```bash
make bootstrap-admin-in-container args="--username admin --email admin@example.com --password 'replace-with-a-strong-secret'"
```

## ถ้าจะพัฒนา worker / async flow

ให้ใช้คำสั่งเพิ่มตามนี้:

- `make up-worker`
- `make logs-worker`
- `make logs-outbox`
- `make replay-dlq`
- `make report-outbox`

และควรดู docs เพิ่มที่:

- [operations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/operations.md)
- [architecture.md](/Users/pluto/Documents/git/fastapi101/docs-thai/architecture.md)

## ถ้าจะพัฒนา quota / billing flow

ตอนนี้ตัวอย่างจริงอยู่ที่:

- `POST /api/v1/items/`
- `GET /api/v1/billing/me/*`
- `GET /api/v1/ops/billing/accounts/{account_id}/*`

เวลาพัฒนาแนวนี้ ให้คิดผ่าน:

- account ownership
- resource key
- feature key
- reserve -> commit/release flow

## เอกสารที่ควรอ่านต่อ

- [api-guide.md](/Users/pluto/Documents/git/fastapi101/docs-thai/api-guide.md)
- [architecture.md](/Users/pluto/Documents/git/fastapi101/docs-thai/architecture.md)
- [configuration.md](/Users/pluto/Documents/git/fastapi101/docs-thai/configuration.md)
- [docs/development.md](/Users/pluto/Documents/git/fastapi101/docs/development.md)
