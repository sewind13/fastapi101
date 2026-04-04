# Security Overview

template นี้มี security baseline ที่ค่อนข้างดีสำหรับ internal platform starter แต่ยังควรถูกมองว่าเป็น starter ไม่ใช่ security product สำเร็จรูป

## สิ่งที่มีแล้ว

- password hashing
- JWT access tokens
- refresh token rotation + revocation
- inactive-user blocking
- auth audit logging
- auth rate limiting
- persisted account lockout
- email verification
- password reset
- webhook guardrails
- metrics auth option

## Password Policy

ระบบรองรับ password policy ผ่าน `SECURITY__*` เช่น:

- minimum length
- uppercase / lowercase / digit / special requirements
- forbid username in password
- forbid email local-part in password

จุดเด่นคือสามารถ tighten policy ใน production ได้โดยไม่ต้องแก้ code

## Email Verification

behavior ปัจจุบัน:

- ถ้าเปิด feature นี้ user ใหม่จะเริ่มด้วย `email_verified=false`
- registration จะ queue verification email ผ่าน outbox/worker flow
- user ที่ auth แล้วสามารถขอส่ง verification ใหม่ได้
- verification link จะ flip `email_verified=true`

endpoint ที่เกี่ยวข้อง:

- `POST /api/v1/auth/verify-email/request`
- `GET /api/v1/auth/verify-email/confirm?token=...`

config ที่เกี่ยวข้อง:

- `APP__PUBLIC_BASE_URL`
- `SECURITY__EMAIL_VERIFICATION_ENABLED`
- `SECURITY__EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES`
- `SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN`

## Password Reset

behavior ปัจจุบัน:

- request จะตอบแบบ generic ไม่ leak ว่ามี email นี้จริงไหม
- ถ้ามี email จริงจะ queue reset email
- confirm reset จะ validate signed token
- password ใหม่ต้องผ่าน policy เดียวกับ registration
- reset สำเร็จจะ clear lockout state ด้วย

endpoint ที่เกี่ยวข้อง:

- `POST /api/v1/auth/password-reset/request`
- `POST /api/v1/auth/password-reset/confirm`

## Auth Flow

endpoint หลัก:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

lifecycle โดยย่อ:

1. user login ด้วย username/password
2. auth service validate credentials
3. app ออก access + refresh tokens
4. access token ใช้กับ protected routes
5. refresh token ใช้หมุนเป็นคู่ใหม่
6. refresh token ที่ใช้แล้วหรือ logout แล้วถูกบันทึกใน revoked token store

## Rate Limiting และ Account Lockout

ระบบมี 2 ชั้นป้องกัน:

1. request-level throttling
2. account-level lockout

rate limiting:

- login จำกัดตาม `IP + username`
- refresh/logout จำกัดตาม client IP
- backend ใช้ได้ทั้ง `memory` และ `redis`

ข้อควรจำ:

- `memory` เหมาะกับ local หรือ single-instance
- `redis` คือ baseline ที่เหมาะกับ production หลาย instance

account lockout:

- failed attempts จะสะสมใน DB
- ชน threshold แล้ว `locked_until` จะถูกตั้ง
- ระหว่าง lock จะตอบ `423 Locked`
- login สำเร็จจะ clear failed state

config สำคัญ:

- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_ENABLED`
- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_MAX_ATTEMPTS`
- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_SECONDS`

## Role Model

role ในระบบตอนนี้คือ baseline authorization model:

- `user`
- `ops_admin`
- `platform_admin`

แนวคิดที่แนะนำ:

- user ปกติใช้ `role="user"`
- คนที่ต้องเข้าถึง `/api/v1/ops/*` ใช้ `ops_admin` หรือ `platform_admin`
- อย่าให้สิทธิ์พิเศษจาก username หรือ email อย่างเดียว

สำคัญ:

- role model ปัจจุบันเป็น secure baseline
- แต่ยังไม่ใช่ RBAC ปลายทางสำหรับ product ใหญ่

ถ้า privileged surfaces โตขึ้น ควรวาง role-permission หรือ policy-based authorization model ต่อ

## Registration Policy

public registration คุมผ่าน `API__PUBLIC_REGISTRATION_ENABLED`

คำแนะนำ:

- ถ้าเป็น public product ค่อยเปิด
- ถ้าเป็น internal-only service หรือ admin backend ควรปิด
- อย่าเปิด public registration พร้อม privileged ops surfaces โดยไม่ review tradeoff

## Outbound Webhook Guardrails

เพื่อกัน SSRF risk ระบบรองรับ:

- `WEBHOOK__REQUIRE_HTTPS=true`
- `WEBHOOK__ALLOW_PRIVATE_TARGETS=false`
- `WEBHOOK__ALLOWED_HOSTS`

แนวทาง production:

- keep HTTPS only
- block private/internal targets
- allowlist เฉพาะ host ที่เชื่อถือ

แต่อย่ามองว่าตัว checks ใน app เป็น defense เดียว ควรมี egress/network controls เพิ่มด้วยถ้าระบบจริงเสี่ยง

## Trusted Proxy Strategy

ถ้า app อยู่หลัง Nginx/Ingress/Load Balancer:

- เปิด `AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS=true` เฉพาะเมื่อไว้ใจ proxy layer จริง
- ตั้ง `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS`
- direct peer ที่ app เห็นต้องอยู่ใน trusted ranges จริง
- อย่า trust forwarded headers จาก arbitrary clients

ถ้าไม่แน่ใจ ให้ปิด trust forwarded headers แล้วใช้ edge rate limiting ก่อน

## สิ่งที่ยังคุ้มทำต่อใน product ที่โตขึ้น

- granular RBAC / permission model
- MFA หรือ step-up auth
- device/session management
- stronger secret rotation playbook
- edge protections ที่ gateway/WAF layer
- asymmetric JWT signing ถ้าต้องมีหลาย service verify token

## Checklist ขั้นต่ำก่อนขึ้น production

- เปลี่ยน `SECURITY__SECRET_KEY`
- ตั้ง `SECURITY__ISSUER` และ `SECURITY__AUDIENCE`
- ตั้ง `API__CORS_ORIGINS`
- เลือกว่าจะ require verified email หรือไม่
- ตัดสินใจเรื่อง public registration
- ถ้า deploy หลาย instance ให้ใช้ Redis-backed rate limiting
- review roles สำหรับ privileged endpoints
- ป้องกัน `/metrics` และ ops endpoints ด้วย network/auth controls
- ถ้าจะเปิด real webhook delivery ให้ตั้ง `WEBHOOK__ALLOWED_HOSTS`

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/security.md](/Users/pluto/Documents/git/fastapi101/docs/security.md)
