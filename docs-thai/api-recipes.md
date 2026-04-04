# API Recipes

ไฟล์นี้รวม flow ที่ใช้บ่อยในรูปแบบหยิบไปลองได้เร็ว ทั้งฝั่ง auth, items example, และ billing self-service

สมมติให้ app รันที่:

- `http://localhost:8000`

และ API prefix คือ:

- `/api/v1`

## 1. สมัครผู้ใช้

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "strongpassword123"
  }'
```

ผลที่คาดหวัง:

- `201 Created`
- response เป็น `UserPublic`

## 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=strongpassword123"
```

ผลที่คาดหวัง:

- `200 OK`
- ได้ `access_token` และ `refresh_token`

## 3. เรียก protected route

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

ผลที่คาดหวัง:

- `200 OK`
- ได้ข้อมูล user ปัจจุบัน

## 4. Refresh token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

## 5. Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

## 6. สร้าง item แบบมี quota

`items` module เป็นตัวอย่างจริงของการต่อ entitlement/quota ใน template นี้ ดังนั้นก่อนลอง `POST /api/v1/items/` ควร grant entitlement `item_create` ให้ account ที่จะใช้ทดสอบก่อน

```bash
curl -X POST http://localhost:8000/api/v1/items/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "First item",
    "description": "Created from the Thai API recipe"
  }'
```

ผลที่คาดหวัง:

- `201 Created`
- response เป็น `ItemPublic`

ถ้า account ไม่มี entitlement `item_create` จะได้:

- `403 Forbidden`
- `error_code = billing.no_entitlement`

## 7. ดู billing summary ของตัวเอง

```bash
curl http://localhost:8000/api/v1/billing/me/summary \
  -H "Authorization: Bearer <access_token>"
```

ผลที่คาดหวัง:

- `200 OK`
- ได้ entitlements ปัจจุบัน
- balances แยกตาม `resource_key`
- recent usage events

## 8. เช็ก balance ของ resource เดียว

```bash
curl http://localhost:8000/api/v1/billing/me/balance/item_create \
  -H "Authorization: Bearer <access_token>"
```

ใช้ดูได้ง่ายว่าก่อนหรือหลังสร้าง item ยังเหลือ `item_create` อีกกี่หน่วย

## 9. ดู usage history แบบมี filter

```bash
curl "http://localhost:8000/api/v1/billing/me/usage?resource_key=item_create&status=committed&sort=desc&offset=0&limit=20" \
  -H "Authorization: Bearer <access_token>"
```

ผลที่คาดหวัง:

- `200 OK`
- ได้ usage history แบบแบ่งหน้า
- มี `total_count`, `has_next`, `has_prev`

filters ที่รองรับ:

- `resource_key`
- `feature_key`
- `status`
- `created_after`
- `created_before`
- `sort`
- `offset`
- `limit`

## 10. ดู usage report แบบ aggregate

```bash
curl "http://localhost:8000/api/v1/billing/me/usage/report?resource_key=item_create" \
  -H "Authorization: Bearer <access_token>"
```

report นี้จะ group ตาม:

- `resource_key`
- `feature_key`
- `status`

เหมาะกับการทำ dashboard หรือสรุป usage แบบไม่ต้องดึง event ทั้งหมด

## 11. flow สำหรับ email verification

1. สมัคร user
2. รับ verification email
3. เรียก `GET /api/v1/auth/verify-email/confirm?token=...`

## 12. flow สำหรับ password reset

1. `POST /api/v1/auth/password-reset/request`
2. รับ reset email
3. `POST /api/v1/auth/password-reset/confirm`

อ่านเวอร์ชันอังกฤษได้ที่ [docs/api-recipes.md](/Users/pluto/Documents/git/fastapi101/docs/api-recipes.md)
