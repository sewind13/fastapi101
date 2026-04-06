# การทำ Database Migrations

ไฟล์นี้อธิบายขั้นตอนการเปลี่ยน schema ของ database ใน template นี้แบบเป็นลำดับใช้งานจริง

สรุปสั้นที่สุด:

- แก้ model ก่อน
- สร้างหรือแก้ Alembic migration
- apply migration กับ stack ที่กำลังรัน
- verify schema ก่อนทำงานต่อ

หลักสำคัญคือ Alembic เป็น schema source of truth ของระบบ และ app ไม่ควรแอบสร้างตารางเองตอน start

## Checklist ที่แนะนำที่สุด

ถ้าอยากได้แค่ checklist เดียวสำหรับใช้จริง ให้ใช้ชุดนี้:

```text
[ ] แก้ SQLModel definition ก่อน
[ ] ถ้ามี model ใหม่ ได้ import ไว้ใน app/db/models/__init__.py และ app/db/base.py แล้ว
[ ] local Compose stack รันอยู่
[ ] สร้าง migration ด้วย make migration m="..."
[ ] review โค้ดใน upgrade() และ downgrade() แล้ว
[ ] เช็ก default, nullability, และ foreign keys แล้ว
[ ] apply migration ด้วย make migrate แล้ว
[ ] verify schema ใน Postgres แล้ว
[ ] รัน lint, typecheck, และ tests แล้ว
```

ชุดนี้คือ happy path ปกติสำหรับ local development

## ไฟล์ที่เกี่ยวข้อง

ไฟล์หลักที่เกี่ยวกับ schema มีประมาณนี้:

- [`app/db/models`](../app/db/models): SQLModel tables
- [`app/db/models/__init__.py`](../app/db/models/__init__.py): import models
- [`app/db/base.py`](../app/db/base.py): metadata discovery ให้ Alembic เห็น schema ครบ
- [`alembic/env.py`](../alembic/env.py): Alembic environment wiring
- [`alembic/versions`](../alembic/versions): migration history
- [`Makefile`](../Makefile): helper commands อย่าง `make migrate` และ `make migration`

## Flow ปกติใน local

ใช้ flow นี้ทุกครั้งที่เพิ่ม table, เพิ่ม column, เปลี่ยน foreign key, หรือเปลี่ยน index

### 1. แก้ model ก่อน

แก้ SQLModel ใน [`app/db/models`](../app/db/models)

ตัวอย่างการเปลี่ยนที่พบบ่อย:

- เพิ่ม table ใหม่
- เพิ่ม column ใหม่
- เพิ่ม foreign key
- เปลี่ยน uniqueness หรือ indexes

ถ้าเพิ่ม model ใหม่ อย่าลืม register ให้ Alembic เห็นด้วยใน:

- [`app/db/models/__init__.py`](../app/db/models/__init__.py)
- [`app/db/base.py`](../app/db/base.py)

ถ้าลืม import สองจุดนี้ บางครั้ง autogenerate จะไม่เห็น table ใหม่เลย

### 2. เปิด local stack

ถ้ายังไม่ได้รัน:

```bash
make up
make ps
```

แนวทางปกติของ repo นี้คือให้ migration รันจากใน `web` container เพื่อให้ config ของ app, Alembic, และ Postgres เป็นชุดเดียวกัน

### 3. สร้าง migration

ใช้คำสั่ง:

```bash
make migration m="describe the schema change"
```

ตัวอย่าง:

```bash
make migration m="add invoice table"
```

คำสั่งนี้จะรัน:

```bash
uv run alembic revision --autogenerate -m "..."
```

จากใน `web` container

### 4. เปิด migration file แล้ว review

หลังสร้างเสร็จ ให้เปิดไฟล์ใหม่ใน [`alembic/versions`](../alembic/versions) แล้วเช็กอย่างน้อย:

- ชื่อตารางถูกไหม
- foreign key ชี้ถูกที่ไหม
- indexes กับ uniqueness ตรงกับ intent ของ model ไหม
- `upgrade()` กับ `downgrade()` สมเหตุสมผลไหม
- มี operation ที่ทำลายข้อมูลโดยไม่ตั้งใจหรือเปล่า

autogenerate เป็นตัวช่วย ไม่ใช่ final truth ดังนั้น migration ที่ซับซ้อนมักต้องแก้มือเพิ่ม

### ตัวอย่าง: เพิ่ม archive fields ให้ `item`

สมมติคุณเพิ่ม field ใน model แบบนี้:

- `is_archived: bool = False`
- `archived_at: datetime | None = None`

ตอน review migration ควรถามอย่างน้อยว่า:

- Alembic เพิ่มทั้งสอง column เข้า `item` จริงไหม
- `is_archived` เป็น nullable/non-nullable ตรงกับที่ตั้งใจไหม
- row เก่ามี default ที่สมเหตุสมผลไหม
- `archived_at` เป็น nullable ไหม
- `downgrade()` ลบ column กลับได้ครบไหม

mindset ที่ดีสำหรับเคสนี้คือ:

1. row เก่าต้องยังใช้ได้
2. row ใหม่ต้องได้ default ที่คาดเดาได้
3. rollback ต้องไม่ทิ้ง schema state แบบครึ่ง ๆ กลาง ๆ

### Pattern สำคัญ: เพิ่ม non-null column ใหม่ให้ table ที่มีข้อมูลอยู่แล้ว

นี่เป็นหนึ่งในจุดที่พลาดกันบ่อยที่สุด

ถ้า table มีข้อมูลอยู่แล้ว การเขียนแบบนี้มักจะพัง:

```python
op.add_column("item", sa.Column("is_archived", sa.Boolean(), nullable=False))
```

เหตุผลที่พังคือ:

- column ใหม่เป็น `NOT NULL`
- row เก่ายังไม่มีค่านี้
- Postgres จะ reject ด้วย `NotNullViolation`

สำหรับ field แบบ `is_archived` pattern ที่ปลอดภัยกว่าคือ:

```python
op.add_column(
    "item",
    sa.Column(
        "is_archived",
        sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),
    ),
)
op.add_column(
    "item",
    sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
)
op.alter_column("item", "is_archived", server_default=None)
```

ทำไมวิธีนี้ถึงดีกว่า:

- row เก่าทั้งหมดจะได้ `false`
- column สุดท้ายยังเป็น `NOT NULL` ได้ตาม intent
- `archived_at` ยังปล่อย nullable ได้
- default ชั่วคราวใน DB สามารถเอาออกทีหลังได้

อีก pattern ที่ถูกต้องเหมือนกันคือ:

1. เพิ่ม column แบบ nullable ก่อน
2. backfill row เก่าด้วย `UPDATE`
3. ค่อย alter ให้เป็น `nullable=False`

ถ้าเพิ่ม non-null column ให้ table ที่มีข้อมูลอยู่แล้ว ให้ใช้หนึ่งในสอง pattern นี้เสมอ

### 5. Apply migration

ใช้:

```bash
make migrate
```

คำสั่งนี้จะรัน:

```bash
uv run alembic upgrade head
```

จากใน `web` container

### 6. Verify หลัง migrate

หลัง apply แล้วควรเช็กก่อนทำอย่างอื่นต่อ

คำสั่งที่ช่วยได้:

```bash
make ps
make logs
make psql
```

จากนั้นรัน quality gates ตามปกติ:

```bash
make lint
make typecheck
uv run pytest -q
```

ถ้า schema change ผูกกับ route หรือ service ด้วย ก็ควรลอง flow นั้นผ่าน Swagger หรือ integration tests ต่อทันที

ตัวอย่างการ verify เองใน `psql`:

```sql
\d item
SELECT id, title, is_archived, archived_at FROM item LIMIT 5;
```

กับ table อื่นก็ใช้หลักเดียวกัน:

- ดูโครง table ด้วย `\d <table_name>`
- ดูข้อมูลจริงสักไม่กี่แถวด้วย `SELECT ... LIMIT ...`

### จุดที่มักงงใน `psql`

ถ้า `psql` ขึ้น prompt แบบนี้:

```text
app-#
```

ส่วนใหญ่แปลว่าคำสั่ง SQL ก่อนหน้ายังไม่จบ โดยสาเหตุที่เจอบ่อยที่สุดคือ **ลืมใส่ `;` ท้ายคำสั่ง**

ตัวอย่าง:

```sql
select * from item limit 10
```

เพราะไม่มี `;` ทำให้ `psql` ยังรอ input ต่อ และยังไม่ execute query

วิธีแก้มี 2 แบบ:

1. ปิด statement ให้ครบด้วย `;`
2. หรือ reset query buffer ปัจจุบันด้วย `\r`

ตัวอย่าง:

```sql
select * from item limit 10;
select count(*) from item;
```

หรือ:

```sql
\r
select * from item limit 10;
```

ความหมายของ prompt:

- `app=#` คือพร้อมรับคำสั่งใหม่
- `app-#` คือคำสั่งก่อนหน้ายังไม่จบ

## หลัง migrate สำเร็จแล้วควรทำอะไรต่อ

เมื่อ `make migrate` ผ่านแล้ว ให้มองว่านี่เป็น “จุดเริ่มของการ verify” ไม่ใช่จบงานทันที

step ที่แนะนำต่อคือ:

1. เปิด `psql` แล้วดู table ที่เพิ่งเปลี่ยน
2. ดูข้อมูลจริงสักไม่กี่แถว
3. ค่อยไปทำ code ส่วนที่อิง schema ใหม่นั้นต่อ
4. รัน tests หรือทดลอง flow จริง

สำหรับตัวอย่าง `item archive` ขั้นต่อที่ใช้งานได้จริงคือ:

```sql
\d item
SELECT id, title, is_archived, archived_at FROM item LIMIT 5;
```

จากนั้นค่อยทำส่วนอื่นของ feature ต่อ:

- response schema
- repository behavior
- service logic
- route wiring
- integration tests

ประเด็นสำคัญคือ migration สำเร็จ แปลแค่ว่า schema เปลี่ยนแล้ว ยังไม่ได้แปลว่า feature เสร็จสมบูรณ์

## เมื่อไหร่ควรแก้ initial migration ใหม่

ถ้ายังเป็น repo ที่เพิ่ง clone มาใหม่และยังไม่ deploy ที่ไหนเลย คุณอาจเลือกแทนที่ initial migration ให้ตรงกับ schema จริงของ product ใหม่ได้

กรณีที่เจอบ่อย:

- จะลบ sample `items` module
- จะแทนที่ schema ตัวอย่างทั้งหมดก่อนขึ้นระบบครั้งแรก
- อยากเริ่มจาก clean initial schema ของ product จริง

แต่ถ้ามี shared environment แล้ว ให้เลิกคิดแบบ “แก้ initial migration ทับ” และใช้ incremental migrations ปกติแทน

หลักจำง่าย:

- ก่อน first deploy: clean initial migration ยังโอเค
- หลังมี environment ร่วม: เพิ่ม migration ใหม่แบบ forward-only

## Flow ตอน deploy

environment ที่จริงจังกว่าควรใช้ flow เดียวกัน:

1. deploy code และ migration ไปพร้อมกัน
2. รัน `alembic upgrade head`
3. ค่อย start หรือ roll app

อย่าพึ่ง `create_all()` หรือ implicit table creation ตอน app start

ใน template นี้ทั้ง API, worker, outbox dispatcher, และ maintenance jobs ต่างสมมติว่า schema อยู่ที่ Alembic revision ที่ถูกต้องแล้ว

## ปัญหา local ที่เจอบ่อย

### code ใหม่กว่า database

อาการที่เจอบ่อย เช่น:

- `column user.email_verified does not exist`
- `column user.account_id does not exist`

ความหมายคือ:

- code เปลี่ยนแล้ว
- local Postgres volume ยังเป็น schema เก่า
- migration ยังไม่ได้ apply หรือ apply ไม่พอ

ให้ลองก่อน:

```bash
make migrate
```

### `make migrate` ผ่าน แต่ schema ยังเพี้ยน

ถ้า local DB นี้ไม่มีข้อมูลสำคัญ และ migration history กับ schema จริงเพี้ยนหนัก อาจต้อง reset local volume แล้วขึ้นใหม่

ตัวอย่าง flow:

```bash
make down
docker volume rm fastapi101_postgres_data
make up
make migrate
```

ใช้เฉพาะกรณีที่ local data ทิ้งได้เท่านั้น

rule of thumb แบบง่าย:

- เริ่มจาก `make migrate` ก่อนเสมอ
- ค่อย reset local volume เมื่อ DB นี้ทิ้งได้และ state เพี้ยนจริง ๆ

### migration fail ด้วย `NotNullViolation`

ถ้าเจอ error ประมาณนี้:

```text
column "is_archived" of relation "item" contains null values
```

ส่วนมากไม่ได้แปลว่าต้อง drop database ใหม่

แต่แปลว่า:

- migration พยายามเพิ่ม `NOT NULL` column
- row เก่าไม่ได้รับ default หรือ backfill value

วิธีแก้ปกติคือ:

1. เปิดไฟล์ migration
2. แก้ให้ใช้ pattern ที่ปลอดภัย เช่น `server_default` หรือ backfill
3. รัน `make migrate` ใหม่

ใน flow ปกติของ Postgres + Alembic ถ้า migration fail มัก rollback ทั้ง transaction อยู่แล้ว ดังนั้นการแก้ไฟล์ migration แล้วรันใหม่มักพอ ไม่จำเป็นต้องล้าง DB ทุกครั้ง

### รัน command จาก host แล้วหา `db` ไม่เจอ

ถ้ารัน command จากเครื่องตรง ๆ แล้วเจอ:

```text
failed to resolve host 'db'
```

สาเหตุคือ `db` เป็น Compose service hostname ใช้ได้จากใน compose network เป็นหลัก ไม่ใช่จาก host shell โดยตรง

ดังนั้นถ้าระบบรันผ่าน Compose อยู่ ให้ใช้คำสั่งแบบ container-aware เช่น:

```bash
make migrate
make bootstrap-admin-in-container
make bootstrap-admin-in-container-env
```

### Alembic ไม่เห็น model ใหม่

เช็กว่า import model ใหม่ไว้ครบใน:

- [`app/db/models/__init__.py`](../app/db/models/__init__.py)
- [`app/db/base.py`](../app/db/base.py)

ถ้า metadata import ไม่ครบ autogenerate อาจไม่เห็น table ใหม่เลย

## Team habit ที่แนะนำ

ทุกครั้งที่มี schema change ให้ทำตามนี้:

1. แก้ model
2. สร้าง migration
3. review migration
4. apply migration ใน local
5. รัน tests
6. ค่อยทำส่วนอื่นต่อ

flow นี้ช่วยลด schema drift และทำให้ debug ปัญหา DB ง่ายขึ้นมาก
