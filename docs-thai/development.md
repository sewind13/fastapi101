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
make up-redis
make down-redis
make ps-redis
make logs-redis
```

ถ้ากำลังจะแก้ table หรือ column ให้เปิด [database-migrations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-migrations.md) ประกบไว้ก่อน เพราะไฟล์นั้นอธิบาย flow การแก้ schema และวิธี debug ปัญหา local DB โดยตรง

ถ้าจะปิด:

```bash
make down
```

## ถ้าจะรัน local แบบมี Redis

repo นี้มี optional compose profile ชื่อ `redis` แล้ว ใช้สำหรับลอง cache, auth rate limiting, worker idempotency หรือ health check แบบ Redis-backed ได้

เริ่ม stack พร้อม Redis:

```bash
make up-redis
```

คำสั่งช่วย:

```bash
make ps-redis
make logs-redis
make down-redis
```

ค่าที่แนะนำถ้าจะให้ app ใน compose คุยกับ Redis ตัวนี้:

```env
CACHE__ENABLED="true"
CACHE__BACKEND="redis"
CACHE__REDIS_URL="redis://redis:6379/2"
AUTH_RATE_LIMIT__BACKEND="redis"
AUTH_RATE_LIMIT__REDIS_URL="redis://redis:6379/0"
WORKER__IDEMPOTENCY_BACKEND="redis"
WORKER__IDEMPOTENCY_REDIS_URL="redis://redis:6379/1"
HEALTH__ENABLE_REDIS_CHECK="true"
HEALTH__REDIS_URL="redis://redis:6379/0"
```

ความหมายของแต่ละชุด config:

- `CACHE__*`
  เปิด application read cache และเก็บค่าลง Redis แทน memory ของแต่ละ process
- `AUTH_RATE_LIMIT__*`
  เก็บ counters ของ auth rate limit ไว้ใน Redis เพื่อให้หลาย app instances ใช้ state ชุดเดียวกัน
- `WORKER__IDEMPOTENCY_*`
  เก็บ idempotency keys ของ worker ไว้ใน Redis เพื่อกัน task ซ้ำข้าม process หรือรอบ retry
- `HEALTH__*`
  ให้ readiness/health check ลอง ping Redis แล้วรายงาน dependency นี้ได้

ทำไมตัวอย่างถึงแยก `/0`, `/1`, `/2`:

- `/0`
  ใช้กับ auth rate limit และ Redis health check
- `/1`
  ใช้กับ worker idempotency
- `/2`
  ใช้กับ application cache

การแยกแบบนี้ไม่บังคับ แต่ช่วยให้ debug และ inspect keys ใน local ง่ายขึ้นมาก

ถ้าจะใช้ Redis ภายนอก compose หรือ managed Redis ก็ใช้ pattern เดิมได้เหมือนกัน แค่เปลี่ยน URL ให้ชี้ไปยัง service นั้น เช่น `redis://host.docker.internal:6379/0`

คำแนะนำแบบ practical:

- local dev: ใช้ compose Redis ได้เลย
- shared env หรือ production-like env: ควรชี้ไป external/managed Redis มากกว่า

### ตัวอย่าง `.env` แบบพร้อมใช้

ถ้าอยากได้จุดเริ่มต้นที่ copy ไปใช้ได้เร็ว ลองเลือกจาก 3 profile นี้

#### 1. ไม่ใช้ Redis

เหมาะกับ local stack ที่ง่ายที่สุด และยังไม่ต้องการ distributed cache, distributed auth rate limiting, หรือ Redis-backed worker idempotency

```env
CACHE__ENABLED="false"
CACHE__BACKEND="memory"

AUTH_RATE_LIMIT__ENABLED="true"
AUTH_RATE_LIMIT__BACKEND="memory"

WORKER__IDEMPOTENCY_ENABLED="true"
WORKER__IDEMPOTENCY_BACKEND="memory"

HEALTH__ENABLE_REDIS_CHECK="false"
```

#### 2. ใช้ Redis แค่ cache

เหมาะกับการลอง application cache ผ่าน Redis แต่ยังอยากให้ rate limit กับ worker idempotency ใช้ค่า in-process เดิม

```env
CACHE__ENABLED="true"
CACHE__BACKEND="redis"
CACHE__REDIS_URL="redis://redis:6379/2"

AUTH_RATE_LIMIT__ENABLED="true"
AUTH_RATE_LIMIT__BACKEND="memory"

WORKER__IDEMPOTENCY_ENABLED="true"
WORKER__IDEMPOTENCY_BACKEND="memory"

HEALTH__ENABLE_REDIS_CHECK="true"
HEALTH__REDIS_URL="redis://redis:6379/0"
```

#### 3. ใช้ Redis เต็มชุด

เหมาะกับการทดสอบทุกตัวอย่างที่ Redis-backed ใน local development

```env
CACHE__ENABLED="true"
CACHE__BACKEND="redis"
CACHE__REDIS_URL="redis://redis:6379/2"

AUTH_RATE_LIMIT__ENABLED="true"
AUTH_RATE_LIMIT__BACKEND="redis"
AUTH_RATE_LIMIT__REDIS_URL="redis://redis:6379/0"

WORKER__IDEMPOTENCY_ENABLED="true"
WORKER__IDEMPOTENCY_BACKEND="redis"
WORKER__IDEMPOTENCY_REDIS_URL="redis://redis:6379/1"

HEALTH__ENABLE_REDIS_CHECK="true"
HEALTH__REDIS_URL="redis://redis:6379/0"
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
