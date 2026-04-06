# เริ่มโปรเจกต์ใหม่

ไฟล์นี้คือคู่มือ day-0/day-1 สำหรับทีมที่เพิ่ง clone template นี้ และอยากเริ่มโปรเจกต์ใหม่ให้ถูกทางตั้งแต่ต้น

เป้าหมายคือ:

- เริ่มรัน local ได้เร็ว
- ไม่เผลอใช้ค่าตัวอย่างที่เสี่ยงใน environment จริง
- รู้ว่าควรแก้อะไรก่อนหลัง

## ภาพรวมขั้นตอนที่แนะนำ

1. copy config ขั้นต่ำ
2. รัน local stack
3. เช็กว่า app กับ DB ขึ้นครบ
4. bootstrap admin คนแรก
5. รัน quality checks
6. ตัดสินใจว่าจะเก็บ example modules/feature layers อะไรไว้

## เริ่มเร็วที่สุด

```bash
cp .env.min.example .env
make up
make ps
```

จากนั้น:

```bash
export BOOTSTRAP_ADMIN_PASSWORD='replace-with-a-strong-secret'
make bootstrap-admin-in-container-env args="--username admin --email admin@example.com --role platform_admin"
make lint
make typecheck
uv run pytest -q
```

## สิ่งที่ควรแก้ทันทีหลัง clone

อย่างน้อยควร review และแก้ค่าพวกนี้:

- `APP__NAME`
- `APP__ENV`
- `DATABASE__URL`
- `SECURITY__SECRET_KEY`
- `SECURITY__ISSUER`
- `SECURITY__AUDIENCE`
- `API__CORS_ORIGINS`
- `API__PUBLIC_REGISTRATION_ENABLED`

ถ้า product จะใช้ email verification หรือ password reset ต้องเช็กเพิ่ม:

- `APP__PUBLIC_BASE_URL`

## `.env.min.example` vs `.env.example`

### ใช้ `/.env.min.example` เมื่อ

- อยากเริ่มเร็ว
- ยังไม่เปิด feature เสริมเยอะ
- อยากคุม config surface ให้เล็กก่อน

### ใช้ `/.env.example` เมื่อ

- อยากดู config ทั้งระบบ
- กำลังจะเปิด worker, metrics, providers, cache, หรือ monitoring
- ต้อง review ว่ามี capability อะไรใน template บ้าง

## ลำดับแนะนำสำหรับ day-0

### 1. ตั้งไฟล์ `.env`

```bash
cp .env.min.example .env
```

จากนั้นแก้ค่าที่จำเป็นก่อน อย่างน้อยคือ:

- app name
- security secret
- issuer/audience
- database URL ถ้าไม่ได้ใช้ค่าตาม compose

### 2. รัน local stack

```bash
make up
make ps
make logs
```

สิ่งที่ควรเห็น:

- `web` container ขึ้น
- `db` container ขึ้น
- app ตอบ `/health/live` ได้

### 3. bootstrap admin คนแรก

โปรเจกต์นี้มี bootstrap command ให้แล้ว ไม่ต้องแก้ SQL มือเป็น path หลัก

ถ้าระบบรันผ่าน Docker Compose อยู่ แนะนำให้ bootstrap จากใน `web` container:

```bash
export BOOTSTRAP_ADMIN_PASSWORD='replace-with-a-strong-secret'
make bootstrap-admin-in-container-env args="--username admin --email admin@example.com --role platform_admin"
```

หรือถ้าจะส่ง password ตรง ๆ:

```bash
make bootstrap-admin-in-container args="--username admin --email admin@example.com --password 'replace-with-a-strong-secret' --role platform_admin"
```

สิ่งที่ command นี้ทำได้:

- สร้าง privileged user ใหม่
- promote user เดิม
- mark ให้ active
- mark ให้ email verified ได้

### 4. ลอง Swagger / login flow

หลัง bootstrap แล้ว ให้ลอง:

1. เปิด `/docs`
2. กด `Authorize`
3. ใส่ `username` และ `password`
4. ลอง `GET /api/v1/auth/me`

ถ้าเก็บ `items` ไว้และอยากลอง quota example ต่อ ให้ grant entitlement `item_create` ก่อน

## ค่าที่ควรระวังเป็นพิเศษ

ก่อนเอาไปใช้ใน shared env หรือ production-like env ควรเช็กอย่างน้อย:

- `SECURITY__SECRET_KEY`
- `DATABASE__URL`
- `API__CORS_ORIGINS`
- `API__PUBLIC_REGISTRATION_ENABLED`
- `METRICS__ENABLED`
- `METRICS__AUTH_TOKEN`
- `AUTH_RATE_LIMIT__REDIS_URL`
- `CACHE__REDIS_URL`
- `WORKER__IDEMPOTENCY_REDIS_URL`
- provider credentials ต่าง ๆ
- broker/Redis URLs ถ้าเปิด worker หรือ cache/rate limiting แบบ distributed

## ค่าที่แนะนำสำหรับ internal service

สำหรับ service ภายในองค์กรทั่วไป ค่าเริ่มต้นที่มักเหมาะคือ:

- `API__PUBLIC_REGISTRATION_ENABLED="false"`
- `METRICS__ENABLED="false"` จนกว่าจะมี internal scrape path พร้อม
- ใช้ Postgres เป็นหลัก
- ใช้ Redis backend เมื่อเปิด rate limiting หรือ cache ใน production จริง

ถ้าจะลอง Redis ใน local repo นี้มี optional compose profile `redis` ให้แล้ว เหมาะกับ development และ smoke test แต่ถ้าเป็น shared env หรือ production-like env ควรเปลี่ยน `*_REDIS_URL` ให้ชี้ไป external/managed Redis มากกว่า

## ถ้าจะลบ example module

ถ้า `items` ไม่ใช่ domain ของระบบ:

1. ตั้ง `EXAMPLES__ENABLE_ITEMS_MODULE="false"`
2. ลบไฟล์ของ items module เมื่อพร้อม
3. สร้าง migration ใหม่ให้ตรงกับ schema จริง
4. ลบ tests ที่เกี่ยวข้อง

ถ้าจะเก็บ `items` ไว้:

- treat มันเป็น reference implementation ของ route -> service -> repository
- และเป็น example ของ entitlement/quota integration

## คำสั่งช่วยตอน debug

```bash
make shell-web
make psql-web
make logs
```

- `make shell-web` ใช้เข้า shell ของ `web` container
- `make psql-web` ใช้ดูว่า `web` container เห็น `DATABASE__URL` เป็นค่าอะไรจริง
- `make logs` ใช้ดู app logs แบบรวม

## Checklist ก่อนถือว่า day-1 พร้อม

- local stack รันได้
- admin คนแรกถูกสร้างแล้ว
- login ผ่าน
- tests/lint/typecheck ผ่าน
- secrets หลักถูกเปลี่ยนแล้ว
- ทีมตัดสินใจแล้วว่าจะเก็บหรือปิด example items module
- ทีมรู้แล้วว่าจะเริ่มจาก `Core` อย่างเดียว หรือเปิด `Extensions`/`Advanced` เพิ่ม

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/bootstrap.md](/Users/pluto/Documents/git/fastapi101/docs/bootstrap.md)
