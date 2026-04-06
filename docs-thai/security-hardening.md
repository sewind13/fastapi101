# Security Hardening Checklist

ใช้ไฟล์นี้เป็น checklist รอบแรกก่อนขึ้น shared env หรือ production-like environment จริง

เป้าหมายของไฟล์นี้ไม่ใช่การออกแบบ security ใหม่ทั้งหมด แต่คือช่วยปิด unsafe defaults, review surfaces ที่ sensitive, และบังคับให้ทีมตัดสินใจเรื่องสำคัญให้ชัดก่อน deploy

## ควรเริ่ม review จากไฟล์ไหนก่อน

- [`app/core/config.py`](/Users/pluto/Documents/git/fastapi101/app/core/config.py)
- [`app/api/deps.py`](/Users/pluto/Documents/git/fastapi101/app/api/deps.py)
- [`app/main.py`](/Users/pluto/Documents/git/fastapi101/app/main.py)
- [`app/api/v1/auth.py`](/Users/pluto/Documents/git/fastapi101/app/api/v1/auth.py)
- [`app/api/v1/ops.py`](/Users/pluto/Documents/git/fastapi101/app/api/v1/ops.py)

## สิ่งที่ควร harden ก่อนใน codebase ปัจจุบัน

### 1. เปลี่ยน JWT secret default ก่อน deploy ทุกครั้ง

ใน code ตอนนี้มี fallback secret ติดมาด้วย:

- [`app/core/config.py`](/Users/pluto/Documents/git/fastapi101/app/core/config.py)

behavior ปัจจุบัน:

- `DEFAULT_SECRET_KEY = "change-me-to-a-32-character-minimum-secret"`
- `SecuritySettings.secret_key` ใช้ค่านี้เป็น default

สิ่งที่ควรทำ:

- ตั้ง `SECURITY__SECRET_KEY` เป็น secret จริงในทุก environment ที่ไม่ใช่ local
- ตอนนี้ app จะ fail ตั้งแต่ startup แล้วถ้า non-local environment ยังใช้ default secret อยู่

เหตุผล:

- ถ้า deploy โดยไม่ override ค่า ใครที่รู้ default นี้ก็มีโอกาส forge token ได้

### 2. ตัดสินใจเรื่อง public registration ให้ชัด

behavior ปัจจุบัน:

- `API__PUBLIC_REGISTRATION_ENABLED` default เป็น `true`
- `POST /api/v1/users/` จะยึดค่าตัวนี้

ไฟล์ที่เกี่ยว:

- [`app/core/config.py`](/Users/pluto/Documents/git/fastapi101/app/core/config.py)
- [`app/api/v1/users.py`](/Users/pluto/Documents/git/fastapi101/app/api/v1/users.py)

สิ่งที่ควรทำ:

- ถ้าเป็น internal tool, admin backend, หรือ staff-only service ให้ปิด
- เปิดเฉพาะกรณีที่ product ตั้งใจให้ public self-signup จริง

### 3. ตัดสินใจว่าจะบังคับ verified email ก่อน login หรือไม่

behavior ปัจจุบัน:

- `SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN` default เป็น `false`

ไฟล์ที่เกี่ยว:

- [`app/core/config.py`](/Users/pluto/Documents/git/fastapi101/app/core/config.py)

สิ่งที่ควรทำ:

- ตัดสินใจให้ชัดว่า product นี้ควรยอมให้ login ก่อน verify email หรือไม่
- ถ้า email identity สำคัญ ควรเปิดใช้งาน

### 4. อย่า expose `/metrics` แบบ public ถ้ายังไม่ป้องกัน

behavior ปัจจุบัน:

- metrics เปิดอยู่เป็น default
- `/metrics` จะถูกป้องกันก็ต่อเมื่อกำหนด `METRICS__AUTH_TOKEN`

ไฟล์ที่เกี่ยว:

- [`app/main.py`](/Users/pluto/Documents/git/fastapi101/app/main.py)

สิ่งที่ควรทำ:

- ให้ `/metrics` อยู่หลัง internal routing หรือ network policy
- หรือกำหนด `METRICS__AUTH_TOKEN` แล้วตั้ง Prometheus ให้ส่ง token นี้

เหตุผล:

- metrics สามารถเผย route names, traffic shape, และ dependency failures ได้

### 5. มอง ops endpoints เป็น privileged surface เสมอ

behavior ปัจจุบัน:

- ops routes อยู่ใต้ `/api/v1/ops/*`
- ใช้ `get_operations_user`
- `OPS__ENABLED` default เป็น `true`

ไฟล์ที่เกี่ยว:

- [`app/api/deps.py`](/Users/pluto/Documents/git/fastapi101/app/api/deps.py)
- [`app/api/v1/ops.py`](/Users/pluto/Documents/git/fastapi101/app/api/v1/ops.py)
- [`app/core/config.py`](/Users/pluto/Documents/git/fastapi101/app/core/config.py)

สิ่งที่ควรทำ:

- เปิด ops routes เฉพาะ environment ที่ต้องใช้จริง
- review คนที่ถือ role `ops_admin` หรือ `platform_admin`
- ถ้าเป็นไปได้อย่า route ops endpoints ออก public internet

### 6. ถ้ามีหลาย instance ให้ใช้ Redis-backed auth rate limiting

behavior ปัจจุบัน:

- auth rate limiting เปิดอยู่
- backend default เป็น `memory`

ไฟล์ที่เกี่ยว:

- [`app/core/config.py`](/Users/pluto/Documents/git/fastapi101/app/core/config.py)
- [`app/api/v1/auth.py`](/Users/pluto/Documents/git/fastapi101/app/api/v1/auth.py)
- [`security.md`](/Users/pluto/Documents/git/fastapi101/docs-thai/security.md)

สิ่งที่ควรทำ:

- ใช้ `AUTH_RATE_LIMIT__BACKEND="redis"` ใน environment ที่มีหลาย replicas
- ตั้ง `AUTH_RATE_LIMIT__REDIS_URL`
- เปิด trusted proxy headers เฉพาะเมื่อ `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS` ถูกต้องแล้ว

เหตุผล:

- `memory` ไม่แชร์ state ข้าม replicas

### 7. ถ้ามีหลาย worker ให้ใช้ Redis-backed idempotency

behavior ปัจจุบัน:

- worker idempotency เปิดอยู่
- backend default เป็น `memory`

ไฟล์ที่เกี่ยว:

- [`app/core/config.py`](/Users/pluto/Documents/git/fastapi101/app/core/config.py)

สิ่งที่ควรทำ:

- ใช้ `WORKER__IDEMPOTENCY_BACKEND="redis"` เมื่อมีหลาย worker instances

### 8. รักษา webhook guardrails ไว้ และกำหนด allowlist ให้ชัด

behavior ปัจจุบัน:

- `require_https=true`
- `allow_private_targets=false`

ไฟล์ที่เกี่ยว:

- [`app/core/config.py`](/Users/pluto/Documents/git/fastapi101/app/core/config.py)

สิ่งที่ควรทำ:

- คงค่าเหล่านี้ไว้
- เพิ่ม `WEBHOOK__ALLOWED_HOSTS` ให้ครบตาม integration ที่ไว้ใจจริง

### 9. ถ้าจะเปิด OTLP telemetry ให้ review เรื่อง transport security

behavior ปัจจุบัน:

- telemetry ปิดอยู่เป็น default
- ถ้าเปิด `exporter_otlp_insecure` default เป็น `true`

ไฟล์ที่เกี่ยว:

- [`app/core/config.py`](/Users/pluto/Documents/git/fastapi101/app/core/config.py)

สิ่งที่ควรทำ:

- ถ้าจะส่ง telemetry ออกนอก trusted local network ให้ review TLS settings ให้ชัดก่อนเปิดใช้งาน

## Minimum hardening decisions ก่อนขึ้น shared env

- [ ] เปลี่ยน `SECURITY__SECRET_KEY`
- [ ] ตั้ง `SECURITY__ISSUER` และ `SECURITY__AUDIENCE` ให้เป็นค่าของ product จริง
- [ ] ตัดสินใจว่า `API__PUBLIC_REGISTRATION_ENABLED` ควรเปิดหรือปิด
- [ ] ตัดสินใจว่า `SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN` ควรเปิดหรือไม่
- [ ] จำกัด `API__CORS_ORIGINS` ให้เหลือเฉพาะ client จริง
- [ ] ป้องกัน `/metrics` ด้วย internal routing หรือ `METRICS__AUTH_TOKEN`
- [ ] review `OPS__ENABLED` และ role assignments ของ ops
- [ ] เปลี่ยน auth rate limiting เป็น Redis ถ้ามีหลาย instances
- [ ] เปลี่ยน worker idempotency เป็น Redis ถ้ามีหลาย workers
- [ ] กำหนด webhook allowlists ให้ explicit

## งาน code hardening ถัดไปที่คุ้มทำ

1. ขยาย startup validation ไปยัง defaults อื่นที่ยังเสี่ยงใน production-like env
2. บังคับให้ startup fail ถ้า multi-instance production-like config ยังใช้ in-memory rate limiting หรือ in-memory worker idempotency
3. เพิ่ม production config validation สำหรับ public registration, metrics protection, และ proxy trust settings
4. เพิ่ม tests ที่ยืนยันว่า validations เหล่านี้ fail แบบปลอดภัย

## เอกสารที่ควรอ่านต่อ

- [security.md](/Users/pluto/Documents/git/fastapi101/docs-thai/security.md)
- [first-deploy-checklist.md](/Users/pluto/Documents/git/fastapi101/docs-thai/first-deploy-checklist.md)
- [deployment.md](/Users/pluto/Documents/git/fastapi101/docs-thai/deployment.md)
- [secret-management.md](/Users/pluto/Documents/git/fastapi101/docs-thai/secret-management.md)
