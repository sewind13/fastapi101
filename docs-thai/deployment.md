# Deployment Guide

ไฟล์นี้อธิบายว่า template นี้ควรถูกนำไปรันนอก local development อย่างไร และมีเรื่องอะไรที่ควรเช็กก่อนถือว่า deployment พร้อม

## แนวคิดหลัก

deployment ที่ดีของ repo นี้ควร:

- ใช้ image เดียวกันระหว่าง app, jobs, worker, และ dispatcher
- ใช้ Alembic migrations เป็น source of truth
- แยก API, worker, และ outbox dispatcher เป็นคนละ process
- มี health checks, metrics, และ monitoring ขั้นต่ำ
- ไม่ใช้ค่าตัวอย่าง local เป็น production secrets

## Production-like Docker Flow

ถ้าจะลอง runtime shape ที่ใกล้ production มากขึ้นใน local ให้ใช้:

```bash
make up-prod
make down-prod
make ps-prod
make logs-prod
```

mode นี้:

- ใช้ image ที่ build แล้วจริง
- ไม่ bind mount source code
- ไม่ต้องติดตั้ง packages ระหว่าง container startup
- ใกล้กับ runtime จริงมากกว่า dev mode
- bind ports เป็น `127.0.0.1` เป็นค่าเริ่มต้นเพื่อให้ปลอดภัยขึ้นใน local
- แยก local credentials ออกจาก production secrets ชัดกว่าเดิม

## Container start flow

web container ปกติจะเริ่มผ่าน script ที่ทำประมาณนี้:

1. `alembic upgrade head`
2. `uvicorn app.main:app --host 0.0.0.0 --port 8000`

ถ้าเปิด worker/outbox:

- worker ควรรันเป็น process แยก
- outbox dispatcher ก็ควรรันเป็น process แยก

แนวทาง production ที่แนะนำ:

- scale worker แยกจาก API
- ใช้ image เดียวกันแต่ command คนละตัว
- ใช้ Redis-backed idempotency ถ้ามีหลาย worker replicas
- lock down ops endpoints ด้วย role model ที่ชัด

## Migration Strategy

Alembic คือ schema source of truth ของระบบนี้

workflow ปกติ:

1. แก้ SQLModel models
2. สร้าง migration
3. apply migration
4. รัน tests

คำสั่งที่เกี่ยวข้อง:

```bash
make migration m="add orders table"
make migrate
make psql
```

สำหรับ deploy จริง ควรเลือกวิธีใดวิธีหนึ่ง:

- init job รัน migration ก่อน app รับ traffic
- release pipeline รัน migration ก่อน switch traffic
- migration job แยกจาก app rollout

สำคัญ:

- อย่า fallback ไปใช้ `create_all()` แทน migration flow

## Health Endpoints

endpoint ที่มี:

- `/health`
- `/health/live`
- `/health/ready`

หลักการใช้:

- `/health/live` สำหรับ liveness
- `/health/ready` สำหรับ readiness
- อย่าใช้ `/health` แทน readiness

readiness อาจเช็ก:

- database
- Redis
- S3
- queue/broker

ขึ้นกับว่าคุณเปิด dependency checks อะไรไว้

## Reverse Proxy / Ingress

ในการ deploy จริง มักมี reverse proxy หรือ ingress อยู่หน้าระบบ

ชั้นนี้มักรับผิดชอบ:

- TLS termination
- public routing
- edge rate limiting / WAF
- forwarded client IP

ถ้าจะ trust `X-Forwarded-For` หรือ `X-Real-IP` ใน app:

- เปิด `AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS=true`
- ตั้ง `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS`
- เช็กให้ชัดว่า direct peer ที่ app เห็นเป็น proxy tier จริง

อย่า trust forwarded IP headers จาก arbitrary clients

### Kubernetes / Ingress note

ถ้าใช้ ingress:

- ใช้ `/health/live` เป็น liveness probe
- ใช้ `/health/ready` เป็น readiness probe
- เช็กว่าการ forward client IP ยังถูกต้องหลัง ingress/load balancer เปลี่ยน
- อย่าปล่อย `/metrics` ไป public route โดยไม่ตั้งใจ

## Metrics และ Monitoring

ถ้าเปิด metrics:

- path หลักคือ `/metrics`
- production ควรมี `METRICS__AUTH_TOKEN`
- ควร scrape ผ่าน internal network
- ไม่ควร expose สู่ public internet โดยไม่ตั้งใจ

baseline metrics ตอนนี้ครอบ:

- HTTP request count / latency / in-flight
- application exceptions
- readiness checks
- auth events
- maintenance jobs
- worker events / queue depth
- outbox dispatch

## Alerting starting points

ตัวอย่าง threshold เริ่มต้น:

- `5xx rate > 1%` นาน 5 นาที
- `p95 latency > 500ms` นาน 10 นาที
- in-flight requests สูงผิดปกตินาน 5-10 นาที
- database readiness failed นาน 2 นาที
- critical dependency readiness failed นาน 2-5 นาที

threshold เหล่านี้ต้อง tune ตาม product จริง ไม่ใช่ใช้เป็นค่าตายตัวเสมอไป

## Rate Limiting ใน production

ถ้ามีหลาย instance:

- ใช้ `AUTH_RATE_LIMIT__BACKEND="redis"`
- ตั้ง `AUTH_RATE_LIMIT__REDIS_URL`

อย่าใช้ `memory` backend เป็น baseline สำหรับ production multi-instance

## Monitoring examples ที่ repo มีให้

repo นี้มีตัวอย่างไฟล์ monitoring เช่น:

- `deploy/monitoring/prometheus.yml`
- `deploy/monitoring/prometheus-alerts.yml`
- `deploy/monitoring/alertmanager.yml`
- Grafana dashboard/provisioning examples
- `docker-compose.monitoring.yml`

local workflow แบบง่าย:

```bash
make up-monitoring
```

จากนั้นเปิด:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Alertmanager: `http://localhost:9093`

## Deployment artifacts ที่มีใน repo

- Kubernetes manifests ใน `deploy/kubernetes`
- Nginx example ใน `deploy/nginx`
- monitoring examples ใน `deploy/monitoring`
- compose files สำหรับ local, monitoring, และ load test

สิ่งเหล่านี้เป็น baseline ไม่ใช่ turnkey production manifests ที่ใช้ได้ทันทีโดยไม่ปรับ

## สิ่งที่ควรมีใน deployment จริง

- app process
- DB ที่ migrate แล้ว
- metrics scraping
- log pipeline
- secret manager / platform secret store
- worker/outbox dispatcher ถ้าเปิด async flow

## Checklist ก่อนถือว่า deploy พร้อม

- เปลี่ยน production secrets แล้ว
- migration ถูก apply แล้ว
- health probes ถูกตั้งถูก path
- metrics ถูกป้องกันด้วย auth/network controls
- ops endpoints ใช้ role ที่ถูกต้อง
- worker/outbox ใช้ broker และ retry/DLQ config ถูกต้อง
- trusted proxy CIDRs ถูกตั้งถูกจริงก่อนเปิด forwarded-header trust
- alert thresholds ถูก tune ตาม profile ของระบบจริง

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/deployment.md](/Users/pluto/Documents/git/fastapi101/docs/deployment.md)
