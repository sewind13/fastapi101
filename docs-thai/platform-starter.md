# Platform Starter คืออะไร

template นี้ควรถูกมองเป็น `production-ready internal platform starter` มากกว่า boilerplate เบา ๆ

เป้าหมายไม่ใช่ทำให้ทุก service เปิดทุก feature ตั้งแต่วันแรก แต่คือให้ทุกทีมเริ่มจากฐานที่แข็งและค่อยเปิดความสามารถเพิ่มได้อย่างเป็นระบบ

## Layer Model

repo นี้ควรถูกใช้งานผ่าน 3 ชั้น:

- `Core`
- `Extensions`
- `Advanced`

กฎง่าย ๆ:

- service ใหม่เริ่มจาก `Core`
- เปิด `Extensions` เมื่อ product มีเหตุผลชัด
- เปิด `Advanced` เมื่อ operational complexity คุ้มกับสิ่งที่ได้

## แต่ละชั้นมีอะไรบ้าง

### Core

สิ่งที่ควรมีแทบทุก service:

- FastAPI app wiring
- versioned routers
- request/response schemas
- service/repository separation
- SQLModel + Alembic
- JWT auth + refresh flow
- centralized errors
- logging
- health/readiness
- Docker dev/prod-like runtime flow
- tests และ type/lint baseline
- API docs และ onboarding docs

ถ้าทีมใช้แค่ Core ก็ควรยังได้:

- boundaries ที่ชัด
- application shape ที่ deploy ได้
- schema migrations ที่ predictable
- auth/error handling ที่นิ่งพอ

### Extensions

สิ่งที่ useful มาก แต่ไม่จำเป็นต้องเปิดตั้งแต่แรก:

- cache layer
- Prometheus metrics
- Grafana/Prometheus/Alertmanager examples
- rate limiting
- provider adapters
- billing / entitlements
- richer security/deployment guidance

แนวคิดคือ feature เหล่านี้ควรรู้สึกว่า “supported และ documented” แต่ยัง optional ในมุม product adoption

### Advanced

สิ่งที่มีภาระ operation สูงขึ้น:

- worker
- transactional outbox
- retry / DLQ
- outbox dispatcher
- ops API
- maintenance jobs
- Kubernetes deployment baselines

สิ่งเหล่านี้มีประโยชน์มาก แต่ควรถูกมองเป็น capability ที่ opt-in ไม่ใช่ assumption ว่าทุกทีมต้องเข้าใจตั้งแต่วันแรก

## Suggested adoption path

สำหรับ internal API ทั่วไป แนะนำแบบนี้:

1. เริ่มจาก `Core`
2. เพิ่ม `Extensions` เมื่อ pain แรกปรากฏจริง
3. เพิ่ม `Advanced` เมื่อ synchronous request handling ไม่พอแล้ว

ตัวอย่าง:

- CRUD API ธรรมดา -> อยู่ใน Core เป็นหลัก
- มี read-heavy endpoint -> พิจารณา cache
- ต้องมี dashboard/alerting -> พิจารณา metrics + monitoring
- ต้องมี async email/webhook fanout -> ขยับไป worker + outbox

## Repo map แบบย่อ

### Core

- `app/main.py`
- `app/api`
- `app/services`
- `app/db`
- `app/schemas`
- `app/core/config.py`
- `app/core/security.py`
- `app/core/logging.py`
- `app/core/health.py`
- `alembic`
- `tests`

### Extensions

- `app/core/cache.py`
- `app/core/metrics.py`
- `app/core/rate_limit.py`
- `app/core/resilience.py`
- `app/core/telemetry.py`
- `app/providers`
- billing/entitlements services และ routes
- monitoring examples

### Advanced

- `app/worker`
- `app/jobs`
- outbox model/repository/service
- `app/api/v1/ops.py`
- `deploy/kubernetes`
- `deploy/nginx/nginx.conf`

## repo นี้เหมาะกับใคร

เหมาะกับ:

- internal APIs ที่อยากได้ production shape ตั้งแต่แรก
- teams ที่ต้องการ auth/security baseline ชัด
- teams ที่จะโตไปถึง metrics, worker, outbox, หรือ quota system

ไม่เหมาะกับ:

- simple demo app ที่ต้องการแค่ route สองสามตัว
- throwaway prototype ที่ไม่อยากมี structure มาก

## คำแนะนำเวลา adopt

- อย่าพยายาม “ใช้ทุกอย่างให้ครบ”
- ให้เลือก feature จาก pain จริงของ product
- ถ้าเปิด Advanced แล้ว ต้องพร้อมรับภาระ operations ของมันด้วย
- ถ้าไม่แน่ใจ เริ่มจาก `Core` แล้วค่อยไล่ดู [adoption-checklists.md](/Users/pluto/Documents/git/fastapi101/docs-thai/adoption-checklists.md)

## Recommendation สุดท้าย

repo นี้ไม่ใช่ tiny boilerplate แล้ว และนั่นไม่ใช่ปัญหา

ถ้ามองมันเป็น:

- strong Core
- supported Extensions
- optional Advanced platform capabilities

มันจะเป็น template ที่ใช้งานได้จริงมากกว่าการพยายามทำให้ทุกอย่างเล็กจนขาด production shape

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/platform-starter.md](/Users/pluto/Documents/git/fastapi101/docs/platform-starter.md)
