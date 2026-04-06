# First Deploy Checklist

ใช้ checklist นี้ก่อน deploy ครั้งแรกใน shared env หรือ production-like environment จริง

## configuration และ secrets

- [ ] เปลี่ยน `SECURITY__SECRET_KEY` เป็นค่าจริงแล้ว
- [ ] `DATABASE__URL` ชี้ไป database จริงของ environment นี้แล้ว
- [ ] `APP__PUBLIC_BASE_URL` ถูกต้องแล้ว
- [ ] `SECURITY__ISSUER` และ `SECURITY__AUDIENCE` เป็นค่าของ product จริง
- [ ] `API__CORS_ORIGINS` จำกัดเฉพาะ origins ที่ควรใช้จริง
- [ ] secrets มาจาก secret manager หรือ platform secret store ที่ควบคุมได้

## database และ migrations

- [ ] Alembic migrations ล่าสุดถูก apply แล้ว
- [ ] ตกลง migration strategy แล้วว่าจะใช้ migration job, init job, หรือ release step
- [ ] มี Postgres backup plan ที่ผ่านการ restore test แล้ว
- [ ] ชัดเจนว่าใครเป็น owner ตอนต้องกู้ database

## runtime topology

- [ ] API รันแยกจาก worker
- [ ] outbox dispatcher รันแยกเมื่อเปิด async flows
- [ ] ตกลง Redis topology แล้วสำหรับ rate limiting, cache, และ idempotency
- [ ] ตกลง broker topology แล้วถ้าเปิด worker features
- [ ] มี ingress หรือ reverse proxy สำหรับ public traffic

## observability

- [ ] metrics ถูกเปิดหรือมีเหตุผลชัดว่า intentionally deferred
- [ ] logs ถูกส่งไป central sink
- [ ] readiness และ liveness probes ชี้ path ถูกต้อง
- [ ] alerts ส่งไป destination ที่มี owner จริง
- [ ] dashboards ครอบ API, worker, และ dependency health

## security hardening

- [ ] public registration ถูกตั้งใจเปิดหรือปิดอย่างชัดเจน
- [ ] ops endpoints จำกัดเฉพาะ privileged roles
- [ ] `/metrics` ถูกป้องกันด้วย auth หรือ internal-only routing
- [ ] trusted proxy headers ยังปิดอยู่ ถ้ายังไม่ได้ตั้ง trusted proxy CIDRs
- [ ] ไม่มี local sample credentials ตกค้างใน manifests หรือ runtime config

## release และ rollback

- [ ] build artifact เป็น immutable และมี version
- [ ] release process รัน migrations ก่อน traffic cutover
- [ ] มี rollback plan เป็นลายลักษณ์อักษร
- [ ] ทีมเข้าใจตรงกันว่า app rollback ไม่เท่ากับ DB restore

## smoke checks หลัง deploy

- [ ] `/health/live` ผ่าน
- [ ] `/health/ready` ผ่าน
- [ ] login ผ่าน
- [ ] protected route อย่างน้อย 1 ตัวผ่าน
- [ ] worker processing ผ่านถ้าเปิด worker
- [ ] outbox publishing ผ่านถ้าเปิด outbox
- [ ] metrics scraping ผ่าน
