# ภาพรวมโครงสร้างระบบ

ไฟล์นี้อธิบายว่าระบบใน template นี้ถูกจัดวางอย่างไร ทำไมต้องแบ่งชั้น และข้อมูลไหลผ่านระบบยังไง

`README` เหมาะกับ onboarding เร็ว ส่วนไฟล์นี้เหมาะกับคนที่จะขยายระบบต่อจริง และอยากเข้าใจเหตุผลของโครงสร้างที่มีอยู่

## เป้าหมายของ architecture นี้

- แยก HTTP concerns ออกจาก business logic
- แยก persistence details ออกจาก route
- ทำให้ schema migration ชัดและ repeatable
- ให้ auth, logging, health, metrics, และ observability ใช้งานได้ตั้งแต่ต้น
- ให้ tests สอดคล้องกับ architecture จริง
- ให้ระบบโตต่อได้โดยไม่กลายเป็น route-heavy CRUD files

## Layer หลัก

- `app/main.py`
  จุดประกอบระบบทั้งหมด
- `app/api`
  route, dependencies, API error mapping
- `app/services`
  business logic
- `app/db`
  models, repositories, sessions, Alembic discovery
- `app/schemas`
  request/response contracts
- `app/core`
  settings, security, logging, health, telemetry, cache, rate limiting
- `app/worker`
  async task publishing, consuming, idempotency, outbox integration

หลักคิดคือแต่ละ layer ควร depend “ลงล่าง” ไปยังสิ่งที่ concrete กว่า ไม่ควรกระโดดข้ามชั้นไปมาแบบไร้ขอบเขต

## Main application wiring

`app/main.py` คือ assembly point ของระบบ

หน้าที่หลัก:

- สร้าง FastAPI app
- load middleware
- ผูก telemetry
- register routers
- define health endpoints
- รวม exception handling ไว้กลางระบบ

ไฟล์นี้ควรยังเป็น declarative wiring เป็นหลัก ถ้าเริ่มมี business rule หนา ๆ โผล่มาที่นี่ แปลว่า architecture กำลัง drift

## Request flow ปกติ

1. request เข้า `app.main`
2. router เลือก endpoint
3. route resolve dependencies
4. route เรียก service
5. service เรียก repository
6. repository คุยกับ database
7. service คืนผล
8. API layer แปลงเป็น response หรือ standardized error

สิ่งสำคัญคือ route ไม่ควรแบก business rule เอง

## API layer

API layer อยู่ที่ `app/api` และ `app/api/v1`

ทำหน้าที่:

- parse request payloads
- inject dependencies
- เรียก services
- map service failures เป็น HTTP
- return response schemas

### Dependencies

`app/api/deps.py` ใช้เก็บ logic กลาง เช่น:

- request-scoped DB session
- current user extraction
- role checks

ข้อดีคือ route ไม่ต้องเขียน auth/session logic ซ้ำทุกไฟล์

### API error mapping

`app/api/errors.py` คือสะพานระหว่าง service-level failures กับ HTTP responses

หลักคิดคือ:

- service ควรอธิบาย failure ในเชิง domain
- API layer ค่อยแปลงเป็น status code

## Service layer

service layer อยู่ที่ `app/services`

นี่คือที่อยู่ของ business logic จริง

service ควรรับผิดชอบ:

- business decisions
- orchestration ข้ามหลาย repository
- transaction boundaries
- การแปลง persistence failures เป็น service-level outcomes

service ไม่ควร:

- return FastAPI response objects
- raise `HTTPException`
- รู้เรื่อง request/response formatting มากเกินจำเป็น

ตัวอย่าง service สำคัญ:

- auth service
- user service
- item service
- entitlement/billing service

## Result pattern

repo นี้ใช้ `ServiceResult` เป็น contract ระหว่าง service layer กับ API layer

ข้อดีคือ:

- test services ได้ง่ายโดยไม่ต้อง spin HTTP handler
- route code บางลง
- error mapping ชัดขึ้น

success path:

- `result.ok = true`
- `result.value` มี payload

failure path:

- `result.ok = false`
- `result.error.code` บอก category ของปัญหา
- `result.error.message` เป็นข้อความที่อ่านได้

## Repository layer

repository layer อยู่ที่ `app/db/repositories`

หน้าที่:

- query details
- inserts/updates
- pagination/filtering
- commit/refresh lifecycle
- row locking หรือ DB-specific behavior

ข้อดีคือถ้าวันหลังเปลี่ยน persistence behavior เราไม่ต้องรื้อ route/service ไปด้วย

## Models vs Schemas

template นี้แยก database models ออกจาก API schemas ชัด

### Models

อยู่ที่ `app/db/models`

ใช้แทน persisted state และ relationships ใน DB

### Schemas

อยู่ที่ `app/schemas`

ใช้ define API contract ที่ client เห็น

เหตุผลที่ต้องแยก:

- database shape แทบไม่เคยตรงกับ external API shape ไปตลอด
- ถ้าไม่แยก วันหลังเปลี่ยน DB internals จะกระทบ client contract ง่าย

## Database sessions และ migrations

`app/db/session.py` ใช้สร้าง engine และ request-scoped sessions

`app/db/base.py` ใช้ import metadata ให้ Alembic เห็น schema ทั้งหมด

ถ้าจะดูภาพรวม table และความสัมพันธ์ของ schema โดยตรง ให้เปิด [database-schema.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-schema.md)

ถ้าจะเปลี่ยน schema จริง ๆ แบบ step-by-step ให้เปิด [database-migrations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-migrations.md)

หลักสำคัญ:

- app ไม่ควรแอบ `create_all()` ตอน start
- Alembic ควรเป็น schema source of truth

แบบนี้ local, CI, staging, และ production จะสอดคล้องกันมากกว่า

## Outbox pattern

template นี้ใช้ transactional outbox pattern สำหรับ broker publishing

flow ระดับสูง:

1. request transaction เขียน domain data และ `outbox_event` พร้อมกัน
2. request success หลัง DB transaction commit
3. outbox dispatcher อ่าน pending rows
4. dispatcher publish เข้า broker
5. worker consume ต่อ

สิ่งที่ pattern นี้ช่วยลด:

- DB commit สำเร็จแต่ publish ไม่สำเร็จ
- process ล่มหลัง commit แต่ก่อน publish
- request ต้องพึ่ง broker connectivity โดยตรงถึงจะ complete ได้

## Authentication architecture

auth ในระบบนี้กระจายอย่างตั้งใจในหลายชั้น:

- `app/core/security.py`
  hashing + token create/decode
- `app/api/deps.py`
  current-user dependency
- `app/services/auth_service.py`
  login / refresh / logout logic
- revoked token model + repository
  เก็บ refresh tokens ที่ถูก revoke ไปแล้ว

แนวคิดสำคัญคือ token lifecycle rules อยู่ใน service layer ไม่ใช่ใน route

## Logging, audit, และ telemetry

observability ส่วนใหญ่กระจุกอยู่ใน:

- `app/core/logging.py`
- `app/core/request.py`
- `app/core/telemetry.py`

ระบบ emit ได้ทั้ง:

- structured JSON logs
- access logs
- exception logs
- audit logs สำหรับ auth/security events

middleware ใน `app/main.py` ยังช่วย attach request IDs, duration, และ metadata เพื่อให้ logs ใช้งานใน production ได้จริง

## Background worker

worker layer อยู่ใน `app/worker`

องค์ประกอบหลัก:

- publisher
- runner
- tasks registry/handlers
- task envelope schemas
- idempotency backend

ปัจจุบันระบบรองรับ baseline ของ:

- retries
- exponential backoff
- dead-letter routing
- idempotency protection
- outbox integration

สิ่งนี้ทำให้ template พร้อมต่อยอดไปสู่:

- email sending
- webhook delivery
- report generation
- third-party sync jobs

## Health และ readiness

health logic อยู่ที่ `app/core/health.py`

endpoint หลัก:

- `/health`
- `/health/live`
- `/health/ready`

สิ่งที่สำคัญจริงในมุม ops คือ `/health/ready` เพราะมัน report ระดับ dependency

แนวคิดคือเพิ่ม checks ใหม่ได้โดยไม่ทำให้ `main.py` บวม

## Example สำคัญใน repo ตอนนี้

### Items module

`items` เป็น example module ที่ครบทั้ง:

- schema
- model
- repository
- service
- route
- tests

และตอนนี้ยังเป็น reference implementation ของ entitlement/quota ด้วย:

- `POST /api/v1/items/` ใช้ feature key `items.create`
- เมื่อสำเร็จจะ consume `item_create` 1 หน่วย
- service จะ reserve quota ก่อน แล้วค่อย commit item + usage accounting

### Billing / Entitlements

โครง billing ที่เพิ่มมาใช้แนวคิด:

- owner ของ quota คือ `account`
- `user` เป็น actor
- `resource_key` คือสิ่งที่นับสิทธิ์จริง
- `feature_key` คือ operation ระดับ request

สิ่งนี้ช่วยให้ต่อไป feature ใหม่ได้โดยไม่ผูกกับ `items` อย่างเดียว

## Core / Extensions / Advanced

วิธีมอง repo นี้ให้ใช้ง่าย:

- `Core`
  API, auth, DB, migrations, tests, health, logging
- `Extensions`
  metrics, rate limiting, cache, providers, billing/entitlements
- `Advanced`
  worker, outbox, DLQ, ops endpoints, monitoring stack, Kubernetes baselines

## เวลาเพิ่ม feature ใหม่ควรคิดยังไง

- ถ้าเป็น CRUD/API ปกติ ให้เดินตาม route -> service -> repository -> model -> schema
- ถ้ามี quota/usage ให้คิดผ่าน entitlement service
- ถ้ามี side effects ที่ไม่ควรบล็อก request ให้คิดเรื่อง worker/outbox
- ถ้าต้องดูแล incident/runbooks ให้เช็กว่าจำเป็นต้องเปิด ops API หรือไม่

## สัญญาณว่า architecture กำลัง drift

- route ยาวมากและมี if/else business logic เยอะ
- service คุย SQLAlchemy โดยตรงแทบทุกที่
- repository รู้เรื่อง auth หรือ current user policy
- migration ไม่สอดคล้องกับ model
- feature ใหม่ข้าม service layer ไปเรื่อย ๆ

อ่านเวอร์ชันอังกฤษแบบละเอียดได้ที่ [docs/architecture.md](/Users/pluto/Documents/git/fastapi101/docs/architecture.md)
