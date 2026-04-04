# Auth สำหรับคนใช้ API

ไฟล์นี้เขียนจากมุมของ frontend/mobile/client developer ที่ต้อง login, refresh token, เรียก protected endpoints, และดู quota/billing ของ account ตัวเอง

## สิ่งที่ต้องรู้ก่อน

- login แล้วจะได้ `access_token` และ `refresh_token`
- `access_token` ใช้เรียก protected endpoints
- `refresh_token` ใช้ขอ token pair ชุดใหม่
- logout จะ revoke refresh token
- บาง account อาจโดน lockout ชั่วคราวจาก failed login attempts
- บางระบบอาจ require verified email ก่อน login ได้

## endpoint หลัก

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/verify-email/request`
- `GET /api/v1/auth/verify-email/confirm?token=...`
- `POST /api/v1/auth/password-reset/request`
- `POST /api/v1/auth/password-reset/confirm`
- `GET /api/v1/billing/me/entitlements`
- `GET /api/v1/billing/me/usage`
- `GET /api/v1/billing/me/usage/report`
- `GET /api/v1/billing/me/balance/{resource_key}`
- `GET /api/v1/billing/me/summary`

## Login

request ใช้ form data:

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
```

fields:

- `username`
- `password`

success response จะได้ประมาณนี้:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "access_expires_in": 1800,
  "refresh_expires_in": 604800
}
```

## เรียก protected endpoints

ให้ส่ง header แบบนี้:

```http
Authorization: Bearer <access_token>
```

ตัวอย่าง route ที่ใช้เช็ก login state ได้ง่ายที่สุดคือ:

- `GET /api/v1/auth/me`

## Refresh token

body:

```json
{
  "refresh_token": "..."
}
```

พฤติกรรมสำคัญ:

- refresh จะ rotate token pair
- refresh token เก่าควรถือว่า invalid หลังใช้งาน
- ถ้าใช้ token ที่ถูก revoke หรือใช้ซ้ำ อาจได้ `401`

## Logout

logout ใช้ refresh token เช่นกัน:

```json
{
  "refresh_token": "..."
}
```

หลัง logout แล้ว token นั้นไม่ควรถูกใช้ต่อ

## ถ้าเจอ error

- `401`
  token ไม่ถูกต้อง, หมดอายุ, login ไม่ผ่าน, หรือ refresh token ใช้ไม่ได้แล้ว
- `403`
  ไม่มีสิทธิ์, account ไม่ active, หรือไม่มี entitlement สำหรับ feature ที่ร้องขอ
- `423`
  account ถูก lockout ชั่วคราว
- `429`
  โดน rate limit

## Best practice ฝั่ง client

- อย่า retry login แบบรัว ๆ
- แยก handle `401` กับ `403`
- เก็บ `request_id` เมื่อมี incident
- อย่าเดาว่า `403` แปลว่า token หมดอายุเสมอไป
- ถ้าระบบมี quota UI ให้ดึง summary/balance ก่อนเรียก feature ที่คิดสิทธิ์ใช้งาน

## Email verification และ password reset

### email verification

flow ปกติ:

1. สมัคร user
2. รับ verification email
3. เปิดลิงก์หรือเรียก `GET /api/v1/auth/verify-email/confirm?token=...`

ถ้าต้องการส่ง verification ใหม่:

- `POST /api/v1/auth/verify-email/request`

### password reset

flow ปกติ:

1. `POST /api/v1/auth/password-reset/request`
2. รับ reset email
3. `POST /api/v1/auth/password-reset/confirm`

ระบบจะตอบ request แบบ generic เพื่อไม่ leak ว่ามี email นี้จริงไหม

## endpoint สำหรับดู quota ของตัวเอง

ถ้า client ต้องแสดงสิทธิ์คงเหลือหรือ usage ของ account ปัจจุบัน ให้ใช้:

- `GET /api/v1/billing/me/entitlements`
- `GET /api/v1/billing/me/usage`
- `GET /api/v1/billing/me/usage/report`
- `GET /api/v1/billing/me/balance/{resource_key}`
- `GET /api/v1/billing/me/summary`

ตัวอย่างเช่น ก่อนเรียก `POST /api/v1/items/` client อาจเช็ก `item_create` ที่ `/api/v1/billing/me/balance/item_create` ก่อนก็ได้

## ความต่างของ billing endpoints

### `GET /api/v1/billing/me/summary`

เหมาะกับหน้า dashboard หรือหน้าแรกหลัง login เพราะคืน:

- entitlements ปัจจุบัน
- balances แยกตาม `resource_key`
- usage ล่าสุด

### `GET /api/v1/billing/me/balance/{resource_key}`

เหมาะกับการเช็กสิทธิ์ของ resource เดียว เช่น `item_create`

### `GET /api/v1/billing/me/usage`

เหมาะกับการแสดง event history แบบแบ่งหน้า

query params ที่รองรับ:

- `resource_key`
- `feature_key`
- `status`
- `created_after`
- `created_before`
- `sort` (`asc` หรือ `desc`)
- `offset`
- `limit`

response จะมี:

- `total_count`
- `has_next`
- `has_prev`
- `usage_events`

ตัวอย่าง:

```http
GET /api/v1/billing/me/usage?feature_key=items.create&sort=desc&limit=20&offset=0
Authorization: Bearer <access_token>
```

### `GET /api/v1/billing/me/usage/report`

เหมาะกับการทำ aggregate/report โดยจะ group ตาม:

- `resource_key`
- `feature_key`
- `status`

และยังใช้ filters อย่าง `resource_key`, `feature_key`, `status`, `created_after`, `created_before` ได้

## ตัวอย่าง flow สำหรับ items quota example

1. login
2. เรียก `GET /api/v1/billing/me/balance/item_create`
3. ถ้าเหลือ quota ค่อยเรียก `POST /api/v1/items/`
4. หลังสร้างเสร็จอาจเรียก `GET /api/v1/billing/me/summary` หรือ `GET /api/v1/billing/me/usage`

## Swagger / OpenAPI notes

ถ้าใช้ Swagger UI:

- กด `Authorize`
- ในโปรเจกต์นี้มักจะเห็น OAuth2 password form
- ให้ใส่ `username` และ `password`
- ปล่อย `client_id` และ `client_secret` ว่างได้ใน flow ปกติ

อ่านต่อได้ที่ [docs-thai/openapi.md](/Users/pluto/Documents/git/fastapi101/docs-thai/openapi.md)

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/auth-for-clients.md](/Users/pluto/Documents/git/fastapi101/docs/auth-for-clients.md)
