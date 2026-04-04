# Operations Guide

ไฟล์นี้รวมเรื่อง day-2 operations ของ template นี้ เช่น maintenance, worker/outbox, account lockout, billing ops, monitoring, และ incident checks เบื้องต้น

สำหรับเรื่อง secret ownership/rotation โดยตรง ให้ดู [secret-management.md](/Users/pluto/Documents/git/fastapi101/docs-thai/secret-management.md) เพิ่ม

## งานดูแลระบบที่ template นี้รองรับ

- cleanup revoked tokens
- ดู outbox summary และ events
- replay DLQ
- ตรวจ auth-state ของ user
- unlock account ที่ถูก lockout
- ดู billing entitlements / usage ของ account
- grant entitlement ให้ account

## คำสั่งที่ใช้บ่อย

- `make cleanup-revoked-tokens`
- `make up-worker`
- `make logs-worker`
- `make logs-outbox`
- `make replay-dlq`
- `make report-outbox`

## Scheduled maintenance

ตัวอย่าง maintenance job ที่ template มีให้:

- cleanup expired rows จาก `revoked_token`

entrypoints ที่เกี่ยวข้อง:

- `make cleanup-revoked-tokens`
- `python -m app.jobs.cleanup_revoked_tokens`

แนวทางที่แนะนำ:

- build image เดียว
- ใช้ image เดียวกันกับ API/worker/jobs
- ให้ jobs รับ config/secret จาก source เดียวกับ app

## ops endpoints ที่สำคัญ

### Outbox / Worker

- `GET /api/v1/ops/outbox/summary`
- `GET /api/v1/ops/outbox/events`
- `POST /api/v1/ops/outbox/replay-dlq`

filters ที่ useful:

- `status`
- `task_name`
- `task_id`

### Auth state / account lockout

- `GET /api/v1/ops/users/{user_id}/auth-state`
- `POST /api/v1/ops/users/{user_id}/unlock`

### Billing / Entitlements

- `GET /api/v1/ops/billing/accounts/{account_id}/entitlements`
- `GET /api/v1/ops/billing/accounts/{account_id}/usage`
- `GET /api/v1/ops/billing/accounts/{account_id}/usage/report`
- `GET /api/v1/ops/billing/accounts/{account_id}/balance/{resource_key}`
- `POST /api/v1/ops/billing/accounts/{account_id}/grant`

ops endpoints ควรเปิดเฉพาะกับผู้ใช้ privileged role เท่านั้น

## Runbook ย่อที่ใช้บ่อย

### 1. Readiness fail

เช็กตามนี้:

1. ดู `/health/ready`
2. เช็ก `DATABASE__URL`
3. ถ้าเปิด Redis/S3/queue checks ให้เช็ก credentials และ network path
4. ดู logs ของ dependency ที่เกี่ยวข้อง

### 2. Migration fail ระหว่าง deploy

1. ดู migration logs ก่อน
2. เช็กว่า target DB มี partial schema change หรือไม่
3. แก้ migration ให้ถูกก่อน re-run rollout
4. อย่า fallback ไปใช้ `create_all()` แทน Alembic

### 3. Login ไม่ผ่านหลายคน

เช็กตามนี้:

1. ดูว่าปัญหาเป็น `401`, `423`, หรือ `429`
2. ถ้าเป็น `423` ใช้ `GET /ops/users/{id}/auth-state`
3. ถ้าจำเป็นค่อยใช้ `POST /ops/users/{id}/unlock`
4. ดู auth metrics ว่ามี failed/rate-limited spike หรือไม่

### 4. Worker ไม่ทำงาน

เช็กตามนี้:

1. `WORKER__ENABLED=true` หรือยัง
2. broker URL ตรงกันทั้ง API และ worker หรือไม่
3. broker/queue reachable หรือไม่
4. worker logs มี failure อะไร
5. outbox dispatcher publish เข้า queue จริงหรือยัง
6. retry queue / DLQ depth โตหรือไม่

### 5. DLQ มี message ค้าง

เช็กตามนี้:

1. หาสาเหตุที่แท้จริงก่อน เช่น provider credentials หรือ payload ผิด
2. แก้ root cause
3. ค่อย replay แบบควบคุมจำนวนได้
4. ดู queue depth และ worker failures ระหว่าง replay

### 6. Outbox โต แต่ queue เงียบ

เช็กตามนี้:

1. outbox dispatcher logs
2. broker connectivity
3. pending rows ใน `outbox_event`
4. `failed` rows
5. ใช้ `make report-outbox` ช่วยสรุปสถานะ

### 7. ลูกค้าบอกว่า quota ไม่ตรง

เช็กตามนี้:

1. ดู `GET /ops/billing/accounts/{account_id}/entitlements`
2. ดู `GET /ops/billing/accounts/{account_id}/balance/{resource_key}`
3. ดู `GET /ops/billing/accounts/{account_id}/usage`
4. ถ้าต้องการ aggregate ใช้ `usage/report`
5. เทียบกับ feature policy ที่ consume quota จริง

## Logging และ observability

สิ่งที่ควรจำ:

- request logs เป็น structured JSON
- audit logs แยก logger name
- request IDs ถูกแนบใน responses และ logs
- readiness/maintenance logs ควรถูกส่งเข้าระบบ log pipeline เดียวกับ app
- local monitoring examples มี Prometheus, Grafana, และ Alertmanager

## Metrics และ alerts ที่ควรดู

- `5xx` rate
- p95 latency
- in-flight requests
- readiness dependency status
- auth failures / rate_limited
- worker failures
- retry queue / DLQ depth
- outbox dispatch failures
- billing usage growth ผิดปกติถ้ามีระบบคิดสิทธิ์ใช้งาน

Prometheus series ที่ useful เช่น:

- `fastapi_template_http_requests_total`
- `fastapi_template_http_request_duration_seconds`
- `fastapi_template_http_requests_in_progress`
- `fastapi_template_app_exceptions_total`
- `fastapi_template_readiness_checks_total`
- `fastapi_template_readiness_dependency_status`
- `fastapi_template_auth_events_total`
- `fastapi_template_worker_events_total`
- `fastapi_template_worker_queue_depth`
- `fastapi_template_outbox_dispatch_events_total`

## Alerting starting points

ตัวอย่าง alert ideas:

- `5xx rate > 1% for 5m`
- `p95 latency > 500ms for 10m`
- in-flight requests สูงผิดปกตินาน 5-10 นาที
- database readiness failed นาน 2 นาที
- login failure spike นาน 10 นาที
- cleanup job failures นาน 15 นาที

## Operational expectations

- worker และ outbox dispatcher ควรรันแยกจาก API
- ใช้ image เดียวกันแต่ command คนละตัว
- ถ้ามีหลาย worker replicas ควรใช้ Redis-backed idempotency
- อย่าเปิด ops endpoints ให้ user ปกติ
- metrics และ ops surface ควรมี network/auth controls เพิ่มจาก app logic เสมอ
- DLQ ควรปกติเป็นค่าว่าง ถ้ามีของค้างแปลว่าต้องตรวจ root cause

## Operational caveats

- `memory` rate limiting ไม่ distributed
- readiness checks validate connectivity ไม่ใช่ end-to-end business health
- queue readiness ไม่ได้แปลว่า consumer throughput ปกติดีเสมอ
- worker stack แม้มี retry/DLQ/outbox แล้ว ก็ยังไม่ใช่ exactly-once guarantee เต็มรูปแบบ

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/operations.md](/Users/pluto/Documents/git/fastapi101/docs/operations.md)
