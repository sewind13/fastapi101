# Observability Guide

ไฟล์นี้สรุป baseline observability ที่ควรเปิดเมื่อจะใช้ template นี้ใน shared env หรือ production-like environment

## เป้าหมาย

ระบบที่พร้อม production ควรตอบคำถามพวกนี้ได้เร็ว:

- API ยัง healthy อยู่ไหม
- dependency หลักต่อได้ไหม
- requests กำลัง fail หรือช้าลงหรือไม่
- workers กำลังค้างหรือไม่
- background tasks กำลังพังหรือไม่

## defaults ที่แนะนำ

สำหรับ shared env หรือ production-like deployment ให้เริ่มจาก:

- structured JSON logs
- request IDs ใน response และ logs
- Prometheus metrics เปิดและ scrape ผ่าน internal network
- readiness checks สำหรับ dependency ที่ใช้งานจริง
- log sink หรือ log aggregator ที่อยู่นอก container
- alerts สำหรับ error rate, latency, saturation, และ queue depth

## logging

template นี้มีอยู่แล้ว:

- structured request logs
- audit logs แยก
- request IDs

production setup ที่แนะนำ:

- ส่ง stdout/stderr เข้า centralized log pipeline
- index `request_id`, path, status code, และ error code
- เก็บ API, worker, และ dispatcher logs ใน platform เดียวกันแต่มี labels แยก workload

## metrics

baseline ที่แนะนำ:

- `METRICS__ENABLED=true`
- scrape ผ่าน internal path
- ตั้ง `METRICS__AUTH_TOKEN` ถ้าใช้ app-level auth ป้องกัน metrics

metrics หลักที่ template มีแล้ว เช่น:

- request totals
- request latency
- in-flight requests
- application exceptions
- readiness dependency status
- auth events
- maintenance jobs
- worker events
- queue depth
- outbox dispatch events

## tracing

ถ้ามี OTLP collector หรือ tracing backend ให้เปิด telemetry เร็วใน shared environments:

- `TELEMETRY__ENABLED=true`
- `TELEMETRY__EXPORTER_OTLP_ENDPOINT=...`
- `TELEMETRY__SERVICE_NAME=...`

baseline ที่แนะนำ:

- เริ่มจาก API traces ก่อน
- ถ้า async flow สำคัญ ค่อยเพิ่ม worker traces
- ให้ logs จับคู่กับ request ID และ trace ID ได้

## alert defaults

threshold เริ่มต้นที่ดี:

- `5xx rate > 1% for 5m`
- `p95 latency > 500ms for 10m`
- in-flight requests สูงผิดปกตินาน 5-10 นาที
- database readiness failed นาน 2 นาที
- Redis readiness failed นาน 5 นาที ถ้า Redis เป็น dependency จริง
- queue depth โตผิดปกติ
- DLQ ไม่เป็นศูนย์นานเกินช่วงตรวจสอบปกติ
- maintenance jobs ล้มเหลวซ้ำ

## workload-specific checks

### API

ดู:

- request rate
- error rate
- p95 และ p99 latency
- readiness status

### Worker

ดู:

- task failures
- duplicate-skip rate
- retry queue depth
- dead-letter queue depth

### Outbox Dispatcher

ดู:

- dispatch failures
- pending outbox growth
- broker connectivity issues

## ค่าตั้งต้นที่ควรเปิดก่อน production

```env
METRICS__ENABLED="true"
METRICS__PATH="/metrics"
METRICS__AUTH_TOKEN="replace-with-real-token"
TELEMETRY__ENABLED="true"
TELEMETRY__SERVICE_NAME="your-service-name"
TELEMETRY__EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317"
```

แล้วค่อยยืนยันว่า:

- Prometheus scrape ผ่าน
- dashboards เห็น traffic จริง
- alerts ส่งไป destination ที่มี owner จริง
- logs ค้นด้วย `request_id` ได้
