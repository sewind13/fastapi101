# Checklist การ Adopt Template

ไฟล์นี้ช่วยให้ทีมตัดสินใจว่าจะใช้ template นี้ในระดับไหน โดยไม่ต้องเปิดทุก subsystem ตั้งแต่วันแรก

แนวคิดสำคัญคือ:

- เริ่มจากสิ่งที่ product ต้องใช้จริง
- เปิด feature เพิ่มเมื่อมีเหตุผลชัด
- ไม่เปิด infrastructure หนักก่อนทีมจะพร้อมดูแล

## วิธีใช้เอกสารนี้

ให้อ่านตามลำดับนี้:

1. เลือก profile ที่ใกล้กับ service ของทีม
2. ใช้ decision matrix เพื่อตัดสินใจเปิด feature เพิ่ม
3. ใช้ checklist ใน layer ที่เลือกเป็นเกณฑ์ก่อนถือว่า adoption เสร็จ

## Layer ของ template

- `Core`
  พื้นฐานที่ service ส่วนใหญ่ควรเริ่มจากจุดนี้
- `Extensions`
  ความสามารถที่ useful มากใน production แต่ไม่จำเป็นต้องเปิดตั้งแต่ commit แรก
- `Advanced`
  ความสามารถด้าน async processing, operations, และ platform runtime ที่มีภาระการดูแลสูงกว่า

## Feature Decision Matrix

| Feature | ควรเปิดเมื่อ | มักยังไม่ต้องเปิดเมื่อ | Layer |
| --- | --- | --- | --- |
| `cache` | read/list endpoint โดนบ่อยและ DB เริ่มเป็น cost ที่รู้สึกได้ | traffic ยังต่ำหรือข้อมูลเปลี่ยนบ่อยจน invalidation เสี่ยง | `Extensions` |
| `metrics` | service ต้อง monitor จริง, ทำ dashboard, หรือมี SLO/alert | ยังเป็น prototype หรือ service สั้นอายุที่ยังไม่มี monitoring expectation | `Extensions` |
| `rate limiting` | auth/public endpoints exposed กว้าง หรือ brute-force protection สำคัญ | service private มากและมี trusted callers ไม่กี่ตัว | `Extensions` |
| `email/webhook providers` | product ต้อง notify user หรือคุยกับ external systems จริง | ตอนนี้ dry-run logs ยังพอและ integration ยังไม่เกิด | `Extensions` |
| `billing / entitlements` | product ต้องขายสิทธิ์ใช้งาน, จำกัด quota, หรือโชว์ balance ให้ลูกค้า | ยังไม่มี paid feature หรือ usage gating | `Extensions` |
| `worker` | request ไม่ควรรองานช้า, งานยาว, email, webhook, report generation | ทุกอย่างยัง synchronous และเร็วพอ | `Advanced` |
| `outbox` | DB write กับ async publishing ต้องสอดคล้องกันมากขึ้น | ยังไม่มี async events หรือ manual resend ยังรับได้ | `Advanced` |
| `ops API` | operator ต้องดู outbox, replay DLQ, unlock account, หรือ grant entitlement | ยังไม่มี async/runtime surface ให้ดูแล | `Advanced` |

กฎง่าย ๆ:

- ถ้า feature แก้ pain ปัจจุบัน ให้เปิด
- ถ้าทีมอธิบายไม่ได้ว่าทำไมเปิดไว้ ให้ปิดก่อน
- ถ้าการเปิด feature ทำให้มี infra เพิ่ม ต้องถามต่อว่าทีมพร้อมดูแล infra นั้นไหม

## วิธีตัดสินใจแบบเร็ว

ถ้าทีมลังเล ให้ถาม 3 คำถามนี้:

1. feature นี้แก้ pain ปัจจุบันหรือ pain ที่ใกล้จะเกิดไหม
2. feature นี้เพิ่ม infra หรือ operational burden อะไรบ้าง
3. ถ้าไม่เปิดวันนี้ ทีมยังส่ง product version แรกได้ไหม

ถ้าคำตอบคือ:

- แก้ pain ชัด
- ทีมพร้อมดูแล
- และการไม่เปิดจะบล็อก product

แปลว่าควรเปิดได้

## Starter Profiles

profile ด้านล่างเป็น guidance ไม่ใช่ product mode แยกชุด เป้าหมายคือให้ทีมเลือกจุดเริ่มต้นได้เร็วโดยไม่ต้องเปิดทุก subsystem พร้อมกัน

## Preset แบบเร็ว

| Preset | เหมาะเมื่อ | Runtime extras | Docker image | Helm shape |
| --- | --- | --- | --- | --- |
| `core-only` | API เป็น request/response กับ Postgres และยังไม่ต้องใช้ Redis หรือ worker | ไม่ต้องเพิ่ม extra | `docker build --tag fastapi-template:core .` | ปิด `worker`, `outboxDispatcher`, Redis checks, cache, metrics และ ops API ถ้ายังไม่ใช้ |
| `redis-enabled` | API ต้องใช้ Redis-backed rate limiting, cache, idempotency หรือ readiness checks | `redis` | `docker build --build-arg RUNTIME_EXTRAS=redis --tag fastapi-template:redis .` | เปิด API ตามปกติ ตั้ง Redis URLs และเปิดเฉพาะ feature ที่ใช้จริง |
| `full-async` | service ต้องใช้ worker + outbox + broker-backed side effects ตั้งแต่ต้น | `all` | `docker build --build-arg RUNTIME_EXTRAS=all --tag fastapi-template:full .` | เปิด API, worker, outbox dispatcher, queue checks, Redis idempotency, ops API และ migration job |

env ตั้งต้นที่ copy ไปปรับต่อได้:

```env
# core-only
CACHE__ENABLED="false"
AUTH_RATE_LIMIT__BACKEND="memory"
METRICS__ENABLED="false"
OPS__ENABLED="false"
WORKER__ENABLED="false"
HEALTH__ENABLE_REDIS_CHECK="false"
HEALTH__ENABLE_QUEUE_CHECK="false"
```

```env
# redis-enabled
CACHE__ENABLED="true"
CACHE__BACKEND="redis"
AUTH_RATE_LIMIT__BACKEND="redis"
HEALTH__ENABLE_REDIS_CHECK="true"
```

```env
# full-async
WORKER__ENABLED="true"
WORKER__IDEMPOTENCY_BACKEND="redis"
OPS__ENABLED="true"
HEALTH__ENABLE_QUEUE_CHECK="true"
```

ตัวอย่าง Helm:

```bash
# core-only
helm upgrade --install api deploy/helm/fastapi-template \
  --set worker.enabled=false \
  --set outboxDispatcher.enabled=false \
  --set config.CACHE__ENABLED=false \
  --set config.METRICS__ENABLED=false \
  --set config.OPS__ENABLED=false \
  --set config.HEALTH__ENABLE_REDIS_CHECK=false \
  --set config.HEALTH__ENABLE_QUEUE_CHECK=false

# redis-enabled
helm upgrade --install api deploy/helm/fastapi-template \
  --set worker.enabled=false \
  --set outboxDispatcher.enabled=false \
  --set config.AUTH_RATE_LIMIT__BACKEND=redis \
  --set config.CACHE__ENABLED=true \
  --set config.CACHE__BACKEND=redis \
  --set config.HEALTH__ENABLE_REDIS_CHECK=true

# full-async
helm upgrade --install api deploy/helm/fastapi-template \
  --set worker.enabled=true \
  --set outboxDispatcher.enabled=true \
  --set config.WORKER__ENABLED=true \
  --set config.WORKER__IDEMPOTENCY_BACKEND=redis \
  --set config.OPS__ENABLED=true \
  --set config.HEALTH__ENABLE_QUEUE_CHECK=true
```

### CRUD API Profile

เหมาะกับ:

- internal CRUD services
- admin backends
- APIs ที่ส่วนใหญ่เป็น request/response ตรงกับ Postgres

ควรเริ่มจาก:

- `Core` only

มักเปิด:

- auth
- migrations
- structured logging
- health/readiness

มักเลื่อนไปก่อน:

- cache
- worker
- outbox
- ops API
- provider adapters

mindset ที่เหมาะ:

- เริ่มให้เรียบที่สุดก่อน แล้วค่อยเปิดของเพิ่มเมื่อ performance หรือ integration กดดันจริง

### Integration API Profile

เหมาะกับ:

- APIs ที่ต้องเรียก external systems
- services ที่ส่ง email หรือ webhook
- services ที่ failure มักมาจาก dependency ภายนอกมากกว่า DB

ควรเริ่มจาก:

- `Core`
- บางส่วนของ `Extensions`

มักเปิด:

- metrics
- rate limiting
- provider adapters
- timeout/retry policy สำหรับ external dependencies

มักเลื่อนไปก่อน:

- worker
- outbox
- ops API

mindset ที่เหมาะ:

- ให้ความสำคัญกับ observability และ dependency safety ตั้งแต่ต้น

### Async Platform Profile

เหมาะกับ:

- services ที่มี side effects เยอะ
- งานที่ต้องใช้ worker/outbox
- ระบบที่มี operator ดู DLQ, queue, และ maintenance flows

ควรเริ่มจาก:

- `Core`
- `Extensions`
- บางส่วนของ `Advanced`

มักเปิด:

- metrics + monitoring stack
- worker
- outbox
- ops API
- cache

mindset ที่เหมาะ:

- มอง service เป็น runtime system มากกว่าแค่ API app และเตรียม day-2 operations ตั้งแต่ต้น

## ตัวอย่างการเลือก profile

- ถ้าคุณกำลังทำ internal admin API ที่คุยกับ Postgres เป็นหลัก -> เริ่มจาก `CRUD API Profile`
- ถ้าคุณกำลังทำ service ที่ต้องยิง webhook, เรียก provider, ส่ง email -> เริ่มจาก `Integration API Profile`
- ถ้าคุณกำลังทำ service ที่มี worker, jobs, outbox, และ operator ต้อง replay งาน -> เริ่มจาก `Async Platform Profile`

## Checklist: Core Only

ถือว่าเริ่มได้เมื่อ:

- app รัน local ได้ด้วย `make up`
- migrations ทำงานได้
- auth flow ใช้ได้
- tests/lint/typecheck ผ่าน
- health endpoints พร้อม
- secret หลักถูกเปลี่ยนแล้วสำหรับ environment จริง

ทีมควรอ่านอย่างน้อย:

- [bootstrap.md](/Users/pluto/Documents/git/fastapi101/docs-thai/bootstrap.md)
- [development.md](/Users/pluto/Documents/git/fastapi101/docs-thai/development.md)
- [configuration.md](/Users/pluto/Documents/git/fastapi101/docs-thai/configuration.md)
- [security.md](/Users/pluto/Documents/git/fastapi101/docs-thai/security.md)

สรุปง่าย ๆ:

- ถ้า service ยังไม่มี async work และยังไม่ต้องมี monitoring stack เต็ม ให้ path นี้เป็น default

## Checklist: Core + Extensions

ถือว่า adoption ถึงระดับนี้เมื่อ:

- metrics ถูก scrape ได้
- rate limiting ถูกตั้งค่าตาม deployment จริง
- provider credentials/secrets แยกจาก `.env` local แล้ว
- cache และ retry policy ถูกเปิดเฉพาะจุดที่ทีมเข้าใจผลกระทบ
- docs ทีมตัวเองบอกชัดว่าเปิด feature ไหนอยู่บ้าง

ทีมควรอ่านเพิ่ม:

- [deployment.md](/Users/pluto/Documents/git/fastapi101/docs-thai/deployment.md)
- [operations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/operations.md)
- [secret-management.md](/Users/pluto/Documents/git/fastapi101/docs-thai/secret-management.md)

สรุปง่าย ๆ:

- path นี้เหมาะกับ service ที่เริ่มเจอ scale, auth hardening, หรือ outbound integrations จริง

## Checklist: Core + Extensions + Advanced

ถือว่า adoption ถึงระดับนี้เมื่อ:

- worker, outbox, และ dispatcher แยก process จริง
- queue depth, worker failures, และ readiness ถูก monitor แล้ว
- DLQ replay/runbooks ถูกทดสอบ
- ops endpoints ถูกป้องกันด้วย role ที่ถูกต้อง
- ทีมมี incident/runbook ขั้นต่ำสำหรับ auth, worker, outbox, และ billing/entitlements

ทีมควรอ่านเพิ่ม:

- [architecture.md](/Users/pluto/Documents/git/fastapi101/docs-thai/architecture.md)
- [load-testing.md](/Users/pluto/Documents/git/fastapi101/docs-thai/load-testing.md)
- [platform-starter.md](/Users/pluto/Documents/git/fastapi101/docs-thai/platform-starter.md)

สรุปง่าย ๆ:

- path นี้เหมาะกับ service ที่ “ต้อง operate async system” จริง ไม่ใช่แค่มี API อย่างเดียว

## คำแนะนำสุดท้าย

- ถ้าทีมยังไม่แน่ใจ ให้เริ่มจาก `Core`
- ถ้า feature ไหนมีผลกับ infra, monitoring, หรือ security ให้ treat เป็นการตัดสินใจระดับทีม ไม่ใช่แค่ code toggle
- ถ้า product เริ่มขายสิทธิ์ใช้งานหรือมี quota แล้ว ให้เปิด billing/entitlements แบบออกแบบเป็น account-based ตั้งแต่แรก

อ่านฉบับอังกฤษแบบละเอียดได้ที่ [docs/adoption-checklists.md](/Users/pluto/Documents/git/fastapi101/docs/adoption-checklists.md)
