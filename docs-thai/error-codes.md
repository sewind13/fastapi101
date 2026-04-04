# Error Codes

ไฟล์นี้เป็น catalog ภาษาไทยแบบอ่านง่ายของ error codes ที่สำคัญใน template นี้

หลักคิดคือ:

- client ใช้ `status code` แยก flow ระดับสูง
- ใช้ `error_code` แยกเหตุผลแบบละเอียด
- เวลาเกิด incident ให้เก็บ `request_id` ไปด้วยเสมอ

## รูปแบบ error response มาตรฐาน

โดยทั่วไป error จะหน้าตาประมาณนี้:

```json
{
  "success": false,
  "error_code": "auth.invalid_credentials",
  "message": "Invalid username or password.",
  "path": "/api/v1/auth/login",
  "request_id": "..."
}
```

## กลุ่ม auth

### `auth.invalid_credentials`

- HTTP status: `401`
- ใช้เมื่อ username/password ไม่ถูกต้อง

### `auth.invalid_token`

- HTTP status: `401`
- ใช้เมื่อ token ไม่ถูกต้อง, หมดอายุ, หรือเชื่อถือไม่ได้

### `auth.refresh_reused`

- HTTP status: `401`
- ใช้เมื่อ refresh token ถูกใช้ไปแล้วหรือถูก revoke แล้ว

### `auth.rate_limited`

- HTTP status: `429`
- ใช้เมื่อ endpoint กลุ่ม auth โดน rate limit

### `auth.account_locked`

- HTTP status: `423`
- ใช้เมื่อ account ถูก lockout ชั่วคราวจาก failed login attempts

## กลุ่ม user

### `user.conflict`

- HTTP status: `400`
- ใช้เมื่อ username หรือ email ชนกับข้อมูลเดิม

### `user.not_found`

- HTTP status: `404`
- ใช้เมื่อไม่พบ user ที่ร้องขอ

## กลุ่ม billing / entitlement

### `billing.no_entitlement`

- HTTP status: `403`
- ใช้เมื่อ account ไม่มีสิทธิ์ใช้ feature/resource นั้นเลย

### `billing.quota_exhausted`

- HTTP status: `403`
- ใช้เมื่อมี entitlement แต่ใช้ครบ quota แล้ว

### `billing.entitlement_expired`

- HTTP status: `403`
- ใช้เมื่อสิทธิ์หมดอายุแล้ว

### `billing.feature_not_enabled`

- HTTP status: `403`
- ใช้เมื่อ feature นี้ยังไม่ถูกเปิดให้ใช้ใน policy/config ปัจจุบัน

## กลุ่ม infra

### `infra.db_unavailable`

- HTTP status: `503`
- ใช้เมื่อ readiness หรือ operation สำคัญต่อ DB ไม่ได้

## กลุ่ม item / business example

### `item.persist_failed`

- HTTP status: `400`
- ใช้เมื่อ business write ของ item ไม่สำเร็จใน service layer

## กลุ่มทั่วไป

### `common.internal_error`

- HTTP status: `500`
- ใช้เมื่อเกิดความผิดพลาดภายในที่ไม่ได้ map เป็น error code เฉพาะ

### `validation_error`

- HTTP status: `422`
- ใช้เมื่อ request body/query/path ไม่ผ่าน validation

## วิธีใช้ในฝั่ง client

- ใช้ `401` เพื่อบอกว่าต้อง login ใหม่หรือ refresh flow มีปัญหา
- ใช้ `403` เพื่อบอกว่าไม่มีสิทธิ์หรือ quota หมด
- ใช้ `423` เพื่อบอกว่า account ถูก lock ชั่วคราว
- log `request_id` ไว้เสมอเวลาต้องส่งเรื่องให้ backend team

อ่าน catalog อังกฤษฉบับเต็มได้ที่ [docs/error-codes.md](/Users/pluto/Documents/git/fastapi101/docs/error-codes.md)
