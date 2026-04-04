# Draft ระบบสิทธิ์การใช้งานแบบนับครั้ง

ไฟล์นี้เป็น draft ทางเทคนิคสำหรับเพิ่มระบบ entitlement / quota แบบใช้ซ้ำได้ในอนาคต

use case ตั้งต้นคือ:

- ลูกค้าซื้อ `service_a`
- ได้สิทธิ์ใช้งาน `30` ครั้ง
- ทุกครั้งที่เรียก `service_a.run` แล้วสำเร็จ จะถูกหัก `1` หน่วย
- โครงสร้างต้องต่อไป feature อื่นได้

## แนวทางที่เลือก

ให้ใช้ `account` เป็นเจ้าของสิทธิ์ตั้งแต่แรก

ไม่แนะนำให้ใช้ `user` เป็น owner ระยะยาว เพราะพอมีหลาย user ต่อ 1 ลูกค้า ระบบจะเริ่มตันเร็ว

## model ที่ควรมี

### `Account`

ไฟล์เป้าหมาย:

- [app/db/models/account.py](/Users/pluto/Documents/git/fastapi101/app/db/models/account.py)

แนวคิด:

- account คือเจ้าของ quota จริง
- user เป็นสมาชิกของ account

### `FeatureEntitlement`

ไฟล์เป้าหมาย:

- [app/db/models/feature_entitlement.py](/Users/pluto/Documents/git/fastapi101/app/db/models/feature_entitlement.py)

ใช้เก็บว่า account นี้มีสิทธิ์ใช้ `resource_key` อะไร และเหลือเท่าไร

field สำคัญ:

- `account_id`
- `resource_key`
- `units_total`
- `units_used`
- `status`
- `valid_from`
- `valid_until`
- `source_type`
- `source_id`

### `UsageReservation`

ไฟล์เป้าหมาย:

- [app/db/models/usage_reservation.py](/Users/pluto/Documents/git/fastapi101/app/db/models/usage_reservation.py)

เอาไว้จอง quota ก่อนทำงานจริง เพื่อกัน race condition

field สำคัญ:

- `account_id`
- `entitlement_id`
- `feature_key`
- `units_reserved`
- `request_id`
- `status`
- `expires_at`

### `UsageEvent`

ไฟล์เป้าหมาย:

- [app/db/models/usage_event.py](/Users/pluto/Documents/git/fastapi101/app/db/models/usage_event.py)

เป็น ledger ของการใช้งานจริง

field สำคัญ:

- `account_id`
- `entitlement_id`
- `reservation_id`
- `resource_key`
- `feature_key`
- `units`
- `request_id`
- `status`

## policy ของ feature

phase แรกยังไม่ต้องทำเป็น table ก็ได้

เก็บเป็น code/config ก่อน เช่น:

```python
FEATURE_POLICIES = {
    "service_a.run": {
        "resource_key": "service_a",
        "units_per_call": 1,
        "charge_on": "success",
    }
}
```

## repository ที่ควรมี

- [app/db/repositories/account.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/account.py)
- [app/db/repositories/feature_entitlement.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/feature_entitlement.py)
- [app/db/repositories/usage_reservation.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/usage_reservation.py)
- [app/db/repositories/usage_event.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/usage_event.py)

หน้าที่หลัก:

- หา entitlement ที่ active
- lock row ตอน reserve
- สร้าง reservation
- commit reservation
- release reservation
- สร้าง usage event

## service ที่ควรมี

- [app/services/entitlement_service.py](/Users/pluto/Documents/git/fastapi101/app/services/entitlement_service.py)
- [app/services/billing_service.py](/Users/pluto/Documents/git/fastapi101/app/services/billing_service.py)

method หลัก:

- `get_balance`
- `reserve_feature_usage`
- `commit_reserved_usage`
- `release_reserved_usage`
- `grant_entitlement`

## request flow ที่แนะนำ

สมมติอนาคตมี route:

- `POST /api/v1/service-a/run`

flow:

1. auth user
2. resolve `account_id`
3. map `feature_key -> resource_key`
4. reserve quota
5. ถ้า reserve ไม่ได้ ให้ตอบ error
6. ทำงานจริง
7. success -> commit
8. fail -> release

## error codes ที่ควรเพิ่ม

ใน [app/services/exceptions.py](/Users/pluto/Documents/git/fastapi101/app/services/exceptions.py):

- `billing.no_entitlement`
- `billing.quota_exhausted`
- `billing.entitlement_expired`
- `billing.feature_not_enabled`

## checklist สำหรับ phase 1

1. เพิ่ม models:
   - `account`
   - `feature_entitlement`
   - `usage_reservation`
   - `usage_event`
2. เพิ่ม `account_id` ใน user
3. register model ใน `app/db/base.py`
4. สร้าง Alembic migration
5. เพิ่ม repositories
6. เพิ่ม `EntitlementService`
7. เพิ่ม schemas สำหรับ balance / usage
8. เพิ่ม ops endpoints แบบ read-only
9. เอาไปผูกกับ feature เดียวก่อน เช่น `service_a.run`
10. เขียน tests ครอบ reserve / commit / release

## scope ที่แนะนำสำหรับรอบแรก

ให้ทำแค่นี้ก่อน:

- one-time quota
- ผูกกับ account
- 1 call = 1 unit
- หักเมื่อ success
- ยังไม่ทำ recurring billing
- ยังไม่ทำ payment integration

แบบนี้ lean พอและต่อยอดได้ดี
