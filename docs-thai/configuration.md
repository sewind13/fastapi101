# Configuration Reference

ไฟล์นี้อธิบายว่ากลุ่ม config หลักของ template นี้มีอะไรบ้าง ควรแก้ตัวไหนก่อน และตัวไหนเป็น optional

source of truth จริงอยู่ที่ [app/core/config.py](/Users/pluto/Documents/git/fastapi101/app/core/config.py) ส่วนตัวอย่างค่าดูได้ที่:

- [/.env.min.example](/Users/pluto/Documents/git/fastapi101/.env.min.example)
- [/.env.example](/Users/pluto/Documents/git/fastapi101/.env.example)

## วิธีโหลด config

ระบบใช้ nested environment variables ผ่าน `pydantic-settings`

ตัวอย่าง:

```env
APP__NAME="FastAPI Template"
DATABASE__URL="postgresql+psycopg://app:app@db:5432/app"
SECURITY__ISSUER="your-template"
```

แนวคิดคือ:

- prefix หน้า `__` บอกว่าอยู่ใน settings group ไหน
- ควรใช้ nested format สำหรับโปรเจกต์ใหม่
- `.env.min.example` เหมาะกับการเริ่มเร็ว
- `.env.example` เหมาะกับการดู config surface ทั้งหมด

settings groups ที่สำคัญในระบบนี้ เช่น:

- `APP__*`
- `EXAMPLES__*`
- `API__*`
- `SECURITY__*`
- `AUTH_RATE_LIMIT__*`
- `DATABASE__*`
- `LOGGING__*`
- `TELEMETRY__*`
- `METRICS__*`
- `EXTERNAL__*`
- `EXTERNAL_EVENT_POLICIES__*`
- `CACHE__*`
- `OPS__*`
- `EMAIL__*`
- `WEBHOOK__*`
- `WORKER__*`
- `HEALTH__*`

## วิธีคิดเวลาอ่าน config

แนะนำให้แบ่ง config เป็น 3 กลุ่มในหัว:

- กลุ่มที่ต้องตัดสินใจตั้งแต่วันแรก
- กลุ่มที่เปิดเมื่อ feature นั้นถูกใช้จริง
- กลุ่มที่เกี่ยวกับ production hardening

## กลุ่ม config ที่ต้องรู้ก่อนวันแรก

### `APP__*`

ใช้กำหนด metadata และ environment mode

ตัวที่ควรรู้:

- `APP__NAME`
- `APP__ENV`
- `APP__PUBLIC_BASE_URL`

`APP__PUBLIC_BASE_URL` สำคัญมากเมื่อเปิด email verification หรือ password reset เพราะระบบใช้สร้างลิงก์ที่ส่งให้ user

### `EXAMPLES__*`

ใช้คุม example modules ที่ติดมากับ template

ตัวหลักคือ:

- `EXAMPLES__ENABLE_ITEMS_MODULE`

ถ้า product ไม่ต้องการ `items` example สามารถปิดได้

### `API__*`

ใช้กำหนด:

- API prefix
- CORS
- public registration

ตัวที่ควรตัดสินใจเร็ว:

- `API__V1_PREFIX`
- `API__CORS_ORIGINS`
- `API__PUBLIC_REGISTRATION_ENABLED`

สำหรับ internal-only service มักควรปิด public registration

### `SECURITY__*`

กลุ่มนี้สำคัญที่สุดด้าน auth/security

ตัวหลัก:

- `SECURITY__SECRET_KEY`
- `SECURITY__ISSUER`
- `SECURITY__AUDIENCE`
- password policy ต่าง ๆ
- email verification toggles
- `SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN`

ถ้าจะขึ้น production ต้องเปลี่ยน `SECURITY__SECRET_KEY` ก่อนเสมอ

### `DATABASE__*`

ใช้กำหนด DB connection และ pool

ตัวสำคัญ:

- `DATABASE__URL`
- `DATABASE__POOL_SIZE`
- `DATABASE__MAX_OVERFLOW`
- `DATABASE__POOL_TIMEOUT`

หมายเหตุ:

- code มี fallback เป็น SQLite
- แต่ถ้ารันผ่าน compose ปกติจะ override เป็น Postgres

## กลุ่ม config ที่เปิดเมื่อ feature ถูกใช้จริง

### `AUTH_RATE_LIMIT__*`

ใช้กำหนด auth rate limiting และ account lockout

ตัวหลัก:

- `AUTH_RATE_LIMIT__BACKEND`
- `AUTH_RATE_LIMIT__REDIS_URL`
- `AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS`
- `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS`
- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_ENABLED`
- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_MAX_ATTEMPTS`
- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_SECONDS`

สำหรับ production จริง ถ้ามีหลาย instance ควรใช้ backend เป็น Redis

### `METRICS__*`

ใช้กำหนด Prometheus metrics endpoint

ตัวหลัก:

- `METRICS__ENABLED`
- `METRICS__PATH`
- `METRICS__AUTH_TOKEN`

แนวคิดที่แนะนำ:

- local/dev เปิดเมื่ออยากดู metrics
- production ควรเปิดพร้อม internal scrape path และ auth/network controls

### `CACHE__*`

ใช้กำหนด application-level cache

ตัวหลัก:

- `CACHE__ENABLED`
- `CACHE__BACKEND`
- `CACHE__REDIS_URL`
- `CACHE__DEFAULT_TTL_SECONDS`

เหมาะกับ read-heavy endpoints มากกว่าเขียนทุกอย่างลง cache ตั้งแต่แรก

### `EMAIL__*` และ `WEBHOOK__*`

ใช้กำหนด provider integrations

ตัวอย่าง:

- เปิดส่งจริงหรือ dry-run
- เลือก provider
- timeout/retry overrides
- route-specific webhook configs

ถ้ายังไม่ส่งจริง ให้คง `DRY_RUN=true` ไว้ก่อน

### `EXTERNAL__*` และ `EXTERNAL_EVENT_POLICIES__*`

ใช้กำหนด timeout/retry baseline สำหรับ external dependencies

เหมาะกับ service ที่เริ่มคุย provider หรือ webhook จริง

### `WORKER__*`

ใช้กำหนด worker, broker, retry, DLQ, และ idempotency

ตัวหลัก:

- `WORKER__ENABLED`
- `WORKER__BROKER_URL`
- `WORKER__QUEUE_NAME`
- `WORKER__RETRY_QUEUE_NAME`
- `WORKER__DEAD_LETTER_QUEUE_NAME`
- `WORKER__IDEMPOTENCY_ENABLED`

เปิดกลุ่มนี้เมื่อ service เริ่มมี async side effects จริง

### `HEALTH__*`

ใช้กำหนด readiness checks เพิ่มเติม เช่น:

- Redis
- S3
- queue/broker

อย่าเปิดทุก check ถ้ายังไม่ได้ใช้ dependency นั้นจริง

## กลุ่ม config ที่เกี่ยวกับ production hardening

- secrets และ issuer/audience
- metrics auth
- Redis-backed rate limit/cache
- trusted proxy headers
- provider credentials
- worker idempotency backend

กลุ่มนี้ไม่ควรถูกมองเป็น “ปรับทีหลังค่อยว่ากัน” ถ้าระบบเริ่มจะขึ้น environment จริง

## วิธีเริ่มต้นที่แนะนำ

ถ้าเพิ่งเริ่มโปรเจกต์:

1. copy `/.env.min.example` เป็น `.env`
2. เปลี่ยน `SECURITY__SECRET_KEY`
3. ตั้ง `APP__ENV`
4. เช็ก `DATABASE__URL`
5. ตัดสินใจเรื่อง `API__PUBLIC_REGISTRATION_ENABLED`
6. ยังไม่ต้องเปิด worker/cache/providers ถ้ายังไม่ใช้

## Checklist ก่อนขึ้น environment จริง

- เปลี่ยน secrets ทั้งหมดที่เป็น sample values แล้ว
- ชัดเจนว่า DB ใช้ Postgres หรือ SQLite
- ถ้าเปิด metrics ใน production มี `METRICS__AUTH_TOKEN`
- ถ้าเปิด Redis-backed limiter/cache ตั้ง URL และ credentials ถูกต้อง
- ถ้าเปิด email/webhook providers ใช้ secret manager ไม่ใช่ hardcode ใน repo
- ถ้าเปิด worker ตั้ง broker URL, retry queue, DLQ, และ idempotency backend ถูกต้อง
- ถ้าไว้ใจ proxy headers จริง ต้องตั้ง `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS`

## คำแนะนำสุดท้าย

- อย่าพยายามเติมทุกตัวใน `.env.example` ตั้งแต่วันแรก
- ให้เริ่มจากขั้นต่ำใน `.env.min.example`
- เวลาเปิด feature ใหม่ ค่อยเปิดกลุ่ม config ที่เกี่ยวข้อง
- ถ้า config ตัวไหนมีผลกับ security หรือ production safety ให้ treat เป็นทีม decision ไม่ใช่แค่ local tweak

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/configuration.md](/Users/pluto/Documents/git/fastapi101/docs/configuration.md)
