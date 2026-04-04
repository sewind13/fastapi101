# Load Testing

ไฟล์นี้อธิบายวิธีคิดและ workflow สำหรับ load test template นี้ให้ได้ข้อมูลที่ใช้ตัดสินใจจริง ไม่ใช่แค่ยิงแล้วดูว่าแอปล่มไหม

## เป้าหมายของ load test

สิ่งที่เราควรตอบให้ได้หลังรันคือ:

- bottleneck แรกอยู่ที่ไหน
- p95 / error rate อยู่ระดับไหน
- auth flow รับโหลดได้แค่ไหน
- worker/outbox ตามโหลดทันไหม
- cache และ rate limiting ช่วยจริงหรือไม่
- readiness ยังนิ่งไหมภายใต้โหลด

## ลำดับ scenario ที่แนะนำ

รันตามลำดับนี้:

1. `smoke`
2. `read baseline`
3. `auth burst`
4. `write + async`
5. `soak`

เหตุผลคือ:

- จับ setup issue ก่อน
- ค่อยไล่จาก read-heavy ไป auth-heavy และ async-heavy
- ปิดท้ายด้วยการดู memory/backlog drift ระยะยาว

## scripts ที่มีใน repo

มี k6 scripts ให้แล้วใน `loadtests/k6` เช่น:

- `smoke.js`
- `read_baseline.js`
- `auth_burst.js`
- `write_async.js`
- `soak.js`

และมี helper กลางใน `common.js`

scripts เหล่านี้สมมติว่า app reachable ที่ `BASE_URL` ซึ่งค่า default คือ `http://localhost:8000`

## Environment variables ที่ใช้บ่อย

ตัวอย่าง runtime overrides:

```bash
BASE_URL=http://localhost:8000
USERNAME_PREFIX=k6user
PASSWORD=strongpassword123
ITEMS_ENABLED=true
```

ถ้าปิด `items` example แล้ว ให้ตั้ง:

```bash
ITEMS_ENABLED=false
```

## คำสั่งที่ใช้บ่อย

- `make up-loadtest`
- `make up-loadtest-worker`
- `make loadtest-smoke`
- `make loadtest-read`
- `make loadtest-auth`
- `make loadtest-write`
- `make loadtest-soak`
- `make down-loadtest`
- `make down-loadtest-worker`

ถ้าจะรันเป็นชุด:

- `./scripts/loadtest.sh core`
- `./scripts/loadtest.sh worker`
- `./scripts/loadtest.sh full`
- `make loadtest-all`

## โหมดการรันแบบชุด

- `core`
  รัน `smoke -> read -> auth`
- `worker`
  รัน `smoke -> read -> auth -> write`
- `full`
  รัน `smoke -> read -> auth -> write -> soak`

แนวทางใช้:

- ใช้ `core` สำหรับเช็ก API baseline ก่อน
- ใช้ `worker` เมื่อต้องการดู async path โดยยังไม่วิ่ง soak ยาว
- ใช้ `full` เมื่ออยากได้ staged test ที่ใกล้ระบบจริงมากที่สุด

## Scenario matrix แบบย่อ

- `smoke`
  พิสูจน์ว่า app พร้อมรับการเทส
  ดู `/health/live`, `/health/ready`, `/metrics`

- `read baseline`
  พิสูจน์ว่า read path ปกติยังเร็วภายใต้ concurrency ที่เพิ่มขึ้น
  ดู `/api/v1/auth/me`, `/api/v1/items/`

- `auth burst`
  พิสูจน์ว่า login/refresh/logout ยังนิ่งภายใต้ auth traffic หนาแน่น

- `write + async`
  พิสูจน์ว่า write path และ outbox/worker ยังตามโหลดทัน

- `soak`
  พิสูจน์ว่าระบบไม่ drift ช้า ๆ เช่น memory leak, connection leak, backlog accumulation

## Metrics ที่ควรดูระหว่างรัน

- request rate
- `5xx` rate
- p95 / p99 latency
- in-flight requests
- readiness failures
- queue depth
- worker failures
- outbox dispatch failures
- auth failures / rate-limited events

## สิ่งที่ควรระวังใน repo นี้

- `items` example อาจ consume entitlement ถ้าคุณยิง `POST /items/`
- ถ้าจะเทส async path ต้องเปิด worker/outbox ให้ครบ
- ถ้าจะเทส rate limiting ต้องแยก valid traffic กับ abuse-like traffic
- ถ้าจะเทส cold cache กับ warm cache ต้องวาง sequence ให้ชัด
- ถ้าจะเทส `/metrics` ใน environment ที่ตั้ง `METRICS__AUTH_TOKEN` ต้องเตรียม token ให้ runner ด้วย

## เป้าหมายเชิงผลลัพธ์ที่ควรตั้งก่อนรัน

ตัวอย่างเช่น:

- read endpoint p95 ต่ำกว่า `300ms`
- login p95 ต่ำกว่า `500ms`
- error rate ต่ำกว่า `1%`
- queue backlog ไม่โตไม่หยุดหลัง burst
- readiness ไม่ fail ระหว่าง traffic ปกติ
- DLQ depth เป็น `0` ใน normal test conditions

## หลังรันเสร็จควรตอบให้ได้

- app replica เดียวรับได้กี่ RPS
- DB เริ่มเป็นคอขวดที่จุดไหน
- worker ต้อง scale ตอนไหน
- cache คุ้มกับ workload จริงไหม
- threshold alerts ที่ควรใช้ควรอยู่ประมาณไหน

## ถ้าจะดู dashboard ระหว่างรัน

ถ้าเปิด monitoring stack:

- Grafana อยู่ที่ `http://localhost:3001`
- Prometheus อยู่ที่ `http://localhost:9090`

panel/query ที่ควรดูเป็นอันดับแรก:

- request rate
- `5xx` rate
- p95 latency
- in-flight requests
- auth events
- readiness dependency status
- worker queue depth

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/load-testing.md](/Users/pluto/Documents/git/fastapi101/docs/load-testing.md)
