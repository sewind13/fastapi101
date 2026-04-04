# คู่มือเพิ่ม API ใหม่

ไฟล์นี้เหมาะกับคนที่จะเพิ่ม resource หรือ feature ใหม่ใน template นี้ และอยากทำให้สอดคล้องกับ architecture ที่มีอยู่

## Mental Model

ให้คิดเป็น layered API:

- `app/api`
  รับผิดชอบเรื่อง HTTP เท่านั้น
- `app/services`
  business rules และ orchestration
- `app/db/repositories`
  persistence details
- `app/db/models`
  database tables
- `app/schemas`
  request/response contracts

request flow ปกติคือ:

`Client -> Route -> Service -> Repository -> Database`

## กฎหลักของ repo นี้

- route ไม่ควรมี business logic หนัก
- service ไม่ควรรู้เรื่อง HTTP
- repository ไม่ควรรู้เรื่อง auth/session ของ FastAPI
- migration ต้องใช้ Alembic เป็น source of truth

## ตอนจะเพิ่ม resource ใหม่ต้องแตะอะไรบ้าง

ถ้าจะเพิ่ม feature อย่าง `orders` ปกติจะต้องแตะไฟล์ประมาณนี้:

- `app/schemas/order.py`
- `app/db/models/order.py`
- `app/db/repositories/order.py`
- `app/services/order_service.py`
- `app/api/v1/orders.py`
- `app/api/v1/router.py`
- `alembic/versions/*.py`
- tests ใน `tests/unit` และ `tests/integration`

## Step-by-step ที่แนะนำ

1. ออกแบบ request/response schema ใน `app/schemas`
2. เพิ่มหรือแก้ SQLModel table ใน `app/db/models`
3. register model import ให้ Alembic เห็น
4. เพิ่ม repository functions สำหรับ read/write
5. เพิ่ม service functions ที่คืน `ServiceResult`
6. เพิ่ม route ใน `app/api/v1`
7. register router
8. สร้าง migration
9. เพิ่ม tests

## ถ้าจะเพิ่ม endpoint ใหม่โดยไม่ใช่ resource ใหม่ทั้งก้อน

endpoint ใหม่ไม่ได้แปลว่าต้องมี model ใหม่ทุกครั้ง บางกรณีอาจเป็นแค่:

- action ใหม่บน model เดิม
- list endpoint ที่มี filter เพิ่ม
- summary หรือ report endpoint
- protected ops endpoint
- flow พิเศษของ feature เดิม

ก่อนลงมือ ให้ตอบ 5 ข้อนี้ก่อน:

1. endpoint นี้ทำอะไร
2. รับ input อะไร และคืน output อะไร
3. ต้อง auth หรือเช็ก role ไหม
4. มีผลกับ database ไหม
5. มีผลกับ outbox, worker, หรือ entitlement ไหม

จากนั้นค่อยทำตามลำดับนี้:

1. เพิ่ม request/response schemas ก่อน
2. เพิ่มหรือแก้ model เฉพาะกรณีที่ persisted data เปลี่ยนจริง
3. เพิ่มหรือแก้ repository ถ้ามี query/write ใหม่
4. ใส่ business logic ใน service
5. เพิ่ม route ใน `app/api/v1`
6. register router ถ้าเป็น router file ใหม่
7. เพิ่ม tests
8. อัปเดต docs ถ้า endpoint นี้ควรถูกค้นพบโดย client, developer, หรือ ops

mental model ที่แนะนำ:

`schema -> model/repository -> service -> route -> router -> tests -> docs`

ถ้าไม่มี schema change ก็ไม่จำเป็นต้องแตะ migration เสมอไป และถ้าไม่มี persistence behavior ใหม่ ก็อาจไม่ต้องเพิ่ม repository ใหม่ด้วย

## Route ควรทำอะไร

route ที่ดีใน repo นี้มักจะ:

1. รับ input ผ่าน schema
2. resolve dependencies เช่น DB session หรือ current user
3. เรียก service function
4. map result เป็น response

ตัวอย่างที่ควรดู:

- [app/api/v1/users.py](/Users/pluto/Documents/git/fastapi101/app/api/v1/users.py)
- [app/api/v1/items.py](/Users/pluto/Documents/git/fastapi101/app/api/v1/items.py)
- [app/api/v1/auth.py](/Users/pluto/Documents/git/fastapi101/app/api/v1/auth.py)

เวลาจะเพิ่ม endpoint ใหม่ ให้ถือว่า route เป็นที่สำหรับ:

- parse input
- resolve dependencies
- เรียก service
- คืน response model

ไม่ใช่ที่สำหรับตัดสินใจเชิง business หลัก

## Service ควรทำอะไร

service layer ควรถือ:

- business decisions
- orchestration ข้ามหลาย repository
- mapping repository failures -> service-level outcomes
- transaction boundaries ที่สำคัญ

service ไม่ควร:

- สร้าง `HTTPException` เอง
- รู้เรื่อง FastAPI request/response objects มากเกินจำเป็น
- ยัด SQL ไว้ใน service ตรง ๆ ถ้า repository layer รองรับได้

ถ้า endpoint ใหม่ไม่ใช่แค่ CRUD read ตรง ๆ ส่วนมาก business rule จะควรอยู่ใน service ก่อนเป็นอันดับแรก

## Repository ควรทำอะไร

repository layer ควรถือ:

- query details
- insert/update/delete details
- locking/filtering/pagination details
- DB-specific behavior

repository ไม่ควรถือ:

- policy ว่าใครมีสิทธิ์ทำอะไร
- HTTP semantics

## Example สำคัญ: items + entitlement

ตอนนี้ `items` module เป็นตัวอย่างจริงของการต่อ entitlement/quota เข้ากับ feature business

flow ของ `POST /api/v1/items/` คือ:

1. route ส่ง `request_id` เข้า service
2. service เรียก entitlement layer เพื่อ reserve usage
3. service ทำ business write ของ item
4. ถ้าสำเร็จค่อย commit usage
5. ถ้าล้มเหลวให้ release reservation

สิ่งนี้ทำให้ logic เรื่อง quota อยู่ใน service ไม่หลุดไปอยู่ใน route

## ถ้าจะเพิ่ม feature ที่ต้องคิด usage/quota

pattern ที่แนะนำคือ:

1. กำหนด `feature_key`
2. map ไป `resource_key`
3. reserve usage ก่อนทำงานจริง
4. commit เมื่อสำเร็จ
5. release ถ้าล้มเหลว

ตัวอย่างปัจจุบัน:

- feature key: `items.create`
- resource key: `item_create`

## Tests ที่ควรมี

ขั้นต่ำควรมี:

- schema validation tests
- service tests
- repository tests ถ้ามี query/locking ซับซ้อน
- integration tests สำหรับ route จริง
- migration sanity checks เมื่อ schema เปลี่ยน

## ข้อผิดพลาดที่พบบ่อย

- เอา business rule ไปไว้ใน route
- เริ่มเขียน route ก่อนทั้งที่ยังไม่ชัดว่า input/output contract คืออะไร
- ข้าม service แล้วเรียก repository จาก route ตรง ๆ
- ไม่เพิ่ม migration หลังแก้ model
- ลืมเพิ่ม tests ฝั่ง integration
- ใช้ example module เป็น production feature โดยไม่ rename/clean up

## Checklist ก่อนเปิด PR ของ endpoint ใหม่

ใช้ list นี้เป็น checklist สั้น ๆ ก่อนเปิด PR หรือก่อนสรุปว่างาน endpoint ใหม่เสร็จแล้ว:

```text
[ ] อธิบายได้ชัดว่า endpoint นี้รับอะไร คืนอะไร และต้อง auth แบบไหน
[ ] เพิ่มหรือแก้ request/response schemas ก่อนแล้ว
[ ] business logic อยู่ใน service layer ไม่ได้หลุดไปอยู่ใน route
[ ] เพิ่ม repository เฉพาะเมื่อมี persistence behavior ใหม่จริง
[ ] ถ้า schema เปลี่ยน ได้เพิ่ม Alembic migration แล้ว
[ ] route คืน response model หรือ standardized error แบบชัดเจน
[ ] ถ้าเป็น router file ใหม่ ได้ register router แล้ว
[ ] มี integration tests ครอบ behavior ของ endpoint นี้
[ ] ถ้า logic ซับซ้อน มี unit tests หรือ repository tests เพิ่มแล้ว
[ ] อัปเดต docs แล้ว ถ้า endpoint นี้ควรถูกค้นพบโดย developer, client, หรือ ops
```

ถ้า endpoint นี้มี quota, outbox, worker, หรือ side effect ข้าม subsystem ให้เช็กเพิ่มอีกข้อ:

```text
[ ] side effect ถูก enforce ใน service layer และมี test ผ่าน flow ของ endpoint จริง
```

## Example Walkthrough: เพิ่ม endpoint ใหม่แบบเป็นขั้นตอน

ด้านล่างคือตัวอย่างวิธีคิด endpoint ใหม่แบบ end-to-end โดยไม่กระโดดไปเขียน route ก่อน

โจทย์ตัวอย่าง:

- เพิ่ม `POST /api/v1/items/{item_id}/archive`
- owner ที่ login อยู่สามารถ archive item ของตัวเองได้
- response ควรคืน item ที่อัปเดตแล้ว
- ไม่ต้องมี table ใหม่
- แต่มี persisted state ที่เปลี่ยนจริง

ลำดับการออกแบบที่แนะนำ:

### 1. นิยาม contract ก่อน

ให้ตอบก่อนว่า:

- endpoint นี้ต้องมี request body ไหม หรือ path parameter พอแล้ว
- response จะคืน shape แบบไหน
- ใครมีสิทธิ์เรียกได้
- ถ้าไม่เจอ item หรือไม่ใช่ owner จะตอบอะไร

ในตัวอย่างนี้:

- ใช้ `item_id` จาก path
- ไม่ต้องมี request body
- ต้อง auth
- owner เท่านั้นที่ทำได้
- response คืน item ที่ถูก archive แล้ว

### 2. เช็กก่อนว่าต้องเปลี่ยน schema ไหม

ให้ถามก่อนว่า database ต้องเก็บ state ใหม่หรือไม่

ในตัวอย่างนี้อาจต้องเพิ่ม:

- `is_archived` ใน `item`
- หรือ `archived_at` เพิ่มด้วย

แปลว่าต้อง:

- แก้ model
- สร้าง migration
- review และ apply migration

แต่ถ้า endpoint เป็นแค่ summary ที่คำนวณจากข้อมูลเดิม อาจไม่ต้องแตะ model หรือ migration เลย

### 3. อัปเดต schemas

ก่อนแตะ route ให้กำหนด API shape ก่อน

ตัวเลือกเช่น:

- ใช้ `ItemPublic` เดิมถ้ามันรองรับ field ใหม่แล้ว
- หรือเพิ่ม/แก้ response schema เพื่อให้ client เห็น archived state ชัดเจน

ประเด็นสำคัญคือ response contract ควรถูกออกแบบ ไม่ใช่ปล่อยให้เกิดตาม model โดยบังเอิญ

### 4. เพิ่ม repository behavior

ถ้า endpoint นี้ต้องมี query หรือ write ใหม่ ให้เพิ่มใน repository

ในตัวอย่างนี้อาจมี:

- load item จาก `id`
- เช็กว่า owner ตรงกับ current user
- mark item เป็น archived
- save และ refresh row

### 5. ใส่ business rule ใน service

service ควรเป็นคนตัดสินว่า:

- item มีอยู่จริงไหม
- current user มีสิทธิ์ archive ไหม
- ถ้า item ถูก archive ไปแล้วควรถือว่า success แบบ idempotent หรือควร error
- failure แต่ละแบบควร map เป็น service-level error อะไร

กฎพวกนี้ควรอยู่ใน service ไม่ใช่ใน route

### 6. ค่อยเพิ่ม route เป็นขั้นสุดท้าย

route ที่ดีควรทำแค่นี้:

1. parse `item_id`
2. resolve `current_user` และ `session`
3. เรียก service
4. คืน response model

แบบนี้ route จะยังบางและสอดคล้องกับ pattern ของ repo นี้

### 7. เพิ่ม tests

test ที่ควรมีสำหรับตัวอย่างนี้ เช่น:

- owner archive item ได้สำเร็จ
- user คนอื่น archive ไม่ได้
- ไม่เจอ item แล้วได้ error ที่คาดไว้
- response สะท้อน archived state ถูกต้อง

ขั้นต่ำควรมี:

- service tests สำหรับ business rule
- integration tests สำหรับ behavior ของ endpoint จริง

### 8. อัปเดต docs ถ้า endpoint นี้ควรถูกค้นพบ

ถ้า endpoint นี้เป็นสิ่งที่ client หรือ teammate ควรรู้ ให้พิจารณาอัปเดต:

- API guide หรือ API recipes
- auth-for-clients ถ้า flow การใช้งานเปลี่ยน
- OpenAPI usage examples ถ้าจำเป็น

## Shortcut จำง่าย

ถ้ายังลังเลว่า logic นี้ควรอยู่ตรงไหน ให้ใช้กฎลัดนี้:

- shape ของ request/response -> `schemas`
- shape ของข้อมูลที่เก็บจริง -> `models`
- query หรือ save behavior -> `repositories`
- business decision -> `services`
- HTTP wiring -> `routes`
- การทำให้คนอื่นค้นเจอ -> `docs`

อ่านเวอร์ชันอังกฤษได้ที่ [docs/api-guide.md](/Users/pluto/Documents/git/fastapi101/docs/api-guide.md)
