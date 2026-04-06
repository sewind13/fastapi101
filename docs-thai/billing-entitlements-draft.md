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

แนวคิดสำคัญของระบบนี้คือ:

- owner ของ quota = `account`
- actor ที่ยิง request = `user`
- สิ่งที่ขายหรือจำกัดการใช้ = `resource_key`
- สิ่งที่ request กำลังทำ = `feature_key`

## `feature_key` กับ `resource_key` ต่างกันยังไง

สองตัวนี้เกี่ยวกัน แต่มีหน้าที่คนละแบบ

- `feature_key`
  ใช้ระบุว่า request นี้กำลังทำ action อะไรในระบบ
- `resource_key`
  ใช้ระบุว่า action นี้ต้องไปหัก quota หรือ entitlement bucket ตัวไหน

ตัวอย่าง:

- `items.create`
  คือ `feature_key`
- `items.archive`
  คือ `feature_key`
- `item_create`
  คือ `resource_key`
- `item_archive`
  คือ `resource_key`

rule of thumb:

- ตั้ง `feature_key` ให้สื่อ action ของระบบ
- ตั้ง `resource_key` ให้สื่อ entitlement หรือ quota ที่อยากขาย
- `feature_key` บอกว่าผู้ใช้กำลังทำอะไร
- `resource_key` บอกว่าต้องไปหักสิทธิ์จาก bucket ไหน

การแยกสองอย่างนี้ออกจากกันทำให้ระบบ reuse ได้ดีขึ้น เพราะในอนาคต:

- หลาย feature อาจหักคนละ quota
- หลาย feature อาจแชร์ quota เดียวกัน
- หรือ pricing policy อาจเปลี่ยนได้โดยไม่ต้องเปลี่ยนชื่อ action ทางธุรกิจ

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

ในตัวอย่างนี้:

- `service_a.run` คือ `feature_key`
- `service_a` คือ `resource_key`
- ถ้า request สำเร็จ 1 ครั้ง จะใช้ 1 unit

## ถ้าจะ add policy ให้ feature ใหม่ต้องทำยังไง

ถ้าต้องการทำให้ feature ใหม่ถูกคุมด้วย quota หรือ entitlement แนะนำ flow นี้:

1. เลือก `feature_key`
2. เลือก `resource_key`
3. เพิ่ม mapping ใน `FEATURE_POLICIES`
4. ทำให้ระบบ billing หรือ ops grant entitlement สำหรับ `resource_key` นี้ได้
5. เรียก `reserve_feature_usage(...)` จาก service layer ก่อนทำงานจริง
6. ถ้าสำเร็จค่อย `commit`
7. ถ้าล้มเหลวค่อย `release`

แต่จริง ๆ แล้วมีได้ 2 pattern หลัก และควรเลือกให้เหมาะกับ feature:

- `validate -> reserve -> write -> commit/release`
  เหมาะกับ feature ที่ business validation ควรตอบก่อน เช่น `not_found`, `forbidden`, หรือ `already_archived`
- `reserve -> write -> commit/release`
  เหมาะกับ feature write ตรง ๆ ที่แทบไม่มี pre-validation นอกจาก auth

ตัวอย่าง: ถ้าจะคุม `POST /api/v1/items/{item_id}/archive`

```python
FEATURE_POLICIES = {
    "items.create": {
        "resource_key": "item_create",
        "units_per_call": 1,
        "charge_on": "success",
    },
    "items.archive": {
        "resource_key": "item_archive",
        "units_per_call": 1,
        "charge_on": "success",
    },
}
```

service flow ของ `items.archive` จะเป็นประมาณนี้:

1. โหลด item เป้าหมาย
2. เช็ก `not_found`, ownership, และ `already_archived`
3. resolve `account_id` ของ user ปัจจุบัน
4. เรียก `reserve_feature_usage(..., feature_key="items.archive", ...)`
5. ทำ archive write
6. ถ้าสำเร็จเรียก `commit_reserved_usage(...)`
7. ถ้าพลาดหลัง reserve แล้วให้เรียก `release_reserved_usage(...)`

flow นี้ตั้งใจให้ต่างจาก `items.create` เพราะ implementation ปัจจุบันของ `archive` ต้องการรักษา business errors ที่ specific กว่าไว้ก่อน เช่น:

- `item.not_found`
- `item.forbidden`
- `item.already_archived`

เฉพาะ request ที่ผ่านสามอย่างนี้แล้วเท่านั้น ถึงจะไป reserve quota ของ `item_archive`

ตัวอย่าง: ถ้าจะคุม `POST /api/v1/items/{item_id}/restore`

```python
FEATURE_POLICIES = {
    "items.create": {
        "resource_key": "item_create",
        "units_per_call": 1,
        "charge_on": "success",
    },
    "items.archive": {
        "resource_key": "item_archive",
        "units_per_call": 1,
        "charge_on": "success",
    },
    "items.restore": {
        "resource_key": "item_restore",
        "units_per_call": 1,
        "charge_on": "success",
    },
}
```

service flow ของ `items.restore` จะเป็นประมาณนี้:

1. โหลด item เป้าหมาย
2. เช็ก `not_found`, ownership, และ `not_archived`
3. resolve `account_id` ของ user ปัจจุบัน
4. เรียก `reserve_feature_usage(..., feature_key="items.restore", ...)`
5. ทำ restore write
6. update `restored_at` และเพิ่ม `restore_count`
7. ถ้าสำเร็จเรียก `commit_reserved_usage(...)`
8. ถ้าพลาดหลัง reserve แล้วให้เรียก `release_reserved_usage(...)`

implementation ของ `restore` ใน template ยัง invalidate item-list cache ของ owner หลัง write สำเร็จด้วย เพื่อให้ item ที่เคยถูก archive แล้วกลับมาโผล่ใน `GET /api/v1/items/`

## lifecycle ของ reservation และ usage

ในระบบปัจจุบัน ควรแยกให้ออก 3 จังหวะ:

1. reserve
2. commit
3. แก้ย้อนหลังหลัง commit

### Reserve

`reserve_feature_usage(...)` หมายความว่า:

- หา feature policy เจอแล้ว
- มี active entitlement อยู่จริง
- quota ยังพอ
- มีการสร้าง `usage_reservation` แถวใหม่ด้วยสถานะ `active`

ตอนนี้ยัง **ไม่ถือว่าใช้ quota จริง** เพราะ:

- `units_used` ยังไม่เพิ่ม
- ยังไม่มี committed usage event
- request แค่ "จองสิทธิ์ไว้ก่อน" เท่านั้น

reserve เหมาะกับกรณีที่ต้องกัน concurrent requests ก่อนที่ business write จะเสร็จ

### Commit

`commit_reserved_usage(...)` คือจุดที่ usage กลายเป็นของจริง

ใน implementation ปัจจุบัน commit จะทำสิ่งเหล่านี้:

- เพิ่ม `feature_entitlement.units_used`
- เปลี่ยนสถานะ reservation เป็น `committed`
- สร้าง `usage_event` ที่มีสถานะ `committed`

ดังนั้น commit ควรเกิด **หลังจาก** protected business write สำเร็จแล้วเท่านั้น

ตัวอย่าง:

- สร้าง item สำเร็จ
- archive item สำเร็จ
- `service_a.run` สำเร็จ

rule of thumb:

- ถ้างานหลักสำเร็จแล้ว -> `commit`

### Release

`release_reserved_usage(...)` ใช้กับ reservation ที่ไม่ควรถูกนับเป็น usage จริง

ใน implementation ปัจจุบัน release จะ:

- เปลี่ยนสถานะ reservation เป็น `released`
- ไม่เพิ่ม `units_used`
- ไม่สร้าง committed usage event

ใช้ release เมื่อ request จอง quota ไปแล้ว แต่ protected work ไม่ได้สำเร็จจริง

ตัวอย่าง:

- DB write พังหลัง reserve
- downstream operation พังหลัง reserve
- flow หยุดกลางทางหลังจาก reserve ไปแล้ว

rule of thumb:

- reserve แล้ว แต่งานหลักไม่สำเร็จ -> `release`

### Reverse

`reverse` ไม่เหมือน `release`

reverse ใช้ในกรณีที่ usage ถูก commit ไปแล้ว และต้องการแก้ย้อนหลัง

แปลว่า:

- quota ถูกหักไปแล้ว
- มี committed usage event อยู่แล้ว
- และตอนนี้ต้องมี correction หรือ reconciliation ตามมา

ตัวอย่าง:

- admin คืน usage charge
- reconciliation job ตรวจพบว่าการหักครั้งนั้นไม่ควรเกิด
- มี compensating workflow ที่ต้องยกเลิก usage ที่เคย commit ไปแล้ว

สรุปสั้น ๆ:

- ก่อน commit -> `release`
- หลัง commit -> `reverse`

ระบบใน template ตอนนี้ implement flow ปกติคือ `reserve -> commit/release` เป็นหลัก ส่วนสถานะอย่าง `reversed` ถูกเตรียมไว้ใน reporting/schema สำหรับ correction workflow ภายหลัง ไม่ใช่ normal failure path ของ request ที่ยังไม่ commit

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
