# API Contracts

ไฟล์นี้อธิบาย convention ของ API ที่ client และ backend developer ควรมองว่า stable และพึ่งพาได้

เป้าหมายคือให้ทีมตอบคำถามพวกนี้ได้ชัด:

- success response หน้าตาประมาณไหน
- error response ควร parse อะไร
- status code ในระบบนี้ตีความยังไง
- billing/usage endpoints คืน metadata อะไรให้ client บ้าง

## Base Prefix

API แบบ versioned ถูก mount ใต้:

- `API__V1_PREFIX`
- ค่า default คือ `/api/v1`

ดังนั้น route ส่วนใหญ่ในระบบนี้จะขึ้นต้นด้วย `/api/v1`

## Success Response Conventions

template นี้ใช้ JSON response ปกติร่วมกับ explicit response models

ตัวอย่าง:

- register user -> `201` พร้อม `UserPublic`
- login -> `200` พร้อม `TokenPair`
- list endpoints -> `200` พร้อม array หรือ wrapper model
- logout -> `200` พร้อม `MessageResponse`

schema หลักที่เกี่ยวข้อง:

- [app/schemas/user.py](/Users/pluto/Documents/git/fastapi101/app/schemas/user.py)
- [app/schemas/item.py](/Users/pluto/Documents/git/fastapi101/app/schemas/item.py)
- [app/schemas/token.py](/Users/pluto/Documents/git/fastapi101/app/schemas/token.py)
- [app/schemas/common.py](/Users/pluto/Documents/git/fastapi101/app/schemas/common.py)
- [app/schemas/billing.py](/Users/pluto/Documents/git/fastapi101/app/schemas/billing.py)

## Billing Response Conventions

ฝั่ง billing/self-service/ops จะไม่ค่อยคืน array ดิบอย่างเดียว แต่ใช้ wrapper models เพื่อให้ client ทำ UI ต่อได้ง่ายขึ้น

shape ที่พบบ่อย:

- entitlement list มี `entitlements`
- balance response แยกตาม `resource_key`
- usage history มี:
  - `total_count`
  - `has_next`
  - `has_prev`
  - `usage_events`
- usage report มี `aggregates`

`aggregates` จะ group ตาม:

- `resource_key`
- `feature_key`
- `status`

แนวคิดคือ:

- ถ้า client จะทำหน้า detail/history ใช้ `usage`
- ถ้าจะทำ dashboard หรือ chart แบบ aggregate ใช้ `usage/report`
- ถ้าจะเช็กสิทธิ์คงเหลือไว ๆ ใช้ `balance/{resource_key}` หรือ `summary`

## Error Response Shape

โดยทั่วไป standardized error จะหน้าตาประมาณนี้:

```json
{
  "success": false,
  "error_code": "user.not_found",
  "message": "User not found.",
  "path": "/api/v1/users/999",
  "request_id": "..."
}
```

validation errors อาจมี `details` เพิ่ม เช่น:

```json
{
  "details": [
    {
      "type": "...",
      "loc": ["body", "field_name"],
      "msg": "...",
      "input": "..."
    }
  ]
}
```

สิ่งที่ client ควรใช้:

- `status code` สำหรับ branching ระดับสูง
- `error_code` สำหรับเหตุผลเชิงธุรกิจหรือ infrastructure ที่ละเอียดกว่า
- `request_id` สำหรับ correlate logs/incident

## Status Code ที่พบบ่อย

- `200`
  สำเร็จสำหรับ read/action ปกติ
- `201`
  สร้าง resource สำเร็จ
- `400`
  service-level bad input หรือ conflict เชิงธุรกิจบางประเภท
- `401`
  invalid credentials / invalid token / refresh token ใช้ไม่ได้
- `403`
  ไม่มีสิทธิ์, inactive user, หรือไม่มี entitlement สำหรับ feature นั้น
- `404`
  ไม่พบ resource
- `422`
  request validation ไม่ผ่าน
- `423`
  account ถูก lockout ชั่วคราว
- `429`
  โดน auth rate limiting
- `500`
  internal server error
- `503`
  dependency/readiness ไม่พร้อม

## Error Codes ที่ควรรู้

### กลุ่ม auth

- `auth.invalid_credentials`
- `auth.inactive_user`
- `auth.invalid_token`
- `auth.refresh_reused`
- `auth.rate_limited`
- `auth.account_locked`

### กลุ่ม billing

- `billing.no_entitlement`
- `billing.quota_exhausted`
- `billing.entitlement_expired`
- `billing.feature_not_enabled`

### กลุ่ม user / item / common

- `user.conflict`
- `user.not_found`
- `item.persist_failed`
- `common.internal_error`

### กลุ่ม infra

- `infra.db_unavailable`

catalog ฉบับเต็มอยู่ที่ [docs-thai/error-codes.md](/Users/pluto/Documents/git/fastapi101/docs-thai/error-codes.md)

## ถ้าจะเพิ่ม error code ใหม่ต้องทำอะไรบ้าง

เวลามี business failure ใหม่ stable contract ของ API ไม่ได้มีแค่ข้อความ error แต่ประกอบด้วย:

- service error code
- HTTP status ที่ map ไว้
- standardized error body

flow ที่แนะนำคือ:

1. เพิ่ม code ใหม่ใน [app/services/exceptions.py](/Users/pluto/Documents/git/fastapi101/app/services/exceptions.py)
2. ให้ service คืนผ่าน `self.failure(...)`
3. map status ใน [app/api/errors.py](/Users/pluto/Documents/git/fastapi101/app/api/errors.py)
4. เขียน test ให้เช็กทั้ง `status_code` และ `error_code`

ตัวอย่าง:

- `item.not_found` -> `404`
- `item.forbidden` -> `403`
- `item.already_archived` -> `409`

นี่คือเหตุผลที่ route ใน template นี้มักใช้ `unwrap_result(...)` แทนการประกอบ error response เอง

## Request ID

error responses มาตรฐานจะมี:

- `request_id`

และระบบยังคืน `X-Request-ID` ใน response headers ด้วย

สิ่งนี้มีประโยชน์มากสำหรับ:

- support cases
- debug incident
- trace การยิง request จากฝั่ง client ไปยัง logs ฝั่ง server

## Auth Contract

response จาก login จะมี shape แบบนี้:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "access_expires_in": 1800,
  "refresh_expires_in": 604800
}
```

protected routes คาดหวัง:

```http
Authorization: Bearer <access_token>
```

ส่วน refresh/logout จะใช้ body ประมาณนี้:

```json
{
  "refresh_token": "..."
}
```

## สิ่งที่ client ควรถือเป็น contract

- ชื่อ `error_code`
- shape ของ standardized error
- presence ของ `request_id`
- auth token response shape
- wrapper metadata ของ billing usage (`total_count`, `has_next`, `has_prev`)

ส่วน internal implementation เช่น service/repository internals ไม่ควรถูกถือเป็น client contract

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/api-contracts.md](/Users/pluto/Documents/git/fastapi101/docs/api-contracts.md)
