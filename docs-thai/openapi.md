# OpenAPI / Swagger

template นี้มี OpenAPI docs ให้ใช้งานระหว่างพัฒนา ทั้งสำหรับสำรวจ routes, ลองยิง API, และดู request/response schemas

ไฟล์นี้อธิบายว่าควรใช้ Swagger/OpenAPI ของโปรเจกต์นี้ยังไง โดยเฉพาะจุดที่คนมักงง เช่นปุ่ม `Authorize`

## URL ที่ใช้บ่อย

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI schema: `/api/v1/openapi.json`

โดยทั่วไป:

- `/docs` เหมาะกับการลอง API เร็ว ๆ
- `/redoc` เหมาะกับการอ่านภาพรวม schema
- `/api/v1/openapi.json` เหมาะกับ tooling/client generation

## ใช้ทำอะไรได้บ้าง

- สำรวจ endpoints ที่มีอยู่
- ดู request/response schemas
- ลองยิง API จาก browser
- เช็กว่า contract เปลี่ยนไปหรือยังตอนกำลังพัฒนา
- ใช้ประกอบการ generate API clients

## Recommended Local Workflow

1. รัน app ด้วย `make up`
2. เปิด `/docs`
3. ถ้าต้องการดู raw login response ให้ลอง `POST /api/v1/auth/login`
4. ถ้าจะเรียก protected routes ให้กด `Authorize`
5. ลอง smoke flow หลักของระบบ

## ตอนกด `Authorize` ต้องใส่อะไร

ในโปรเจกต์นี้ Swagger มักจะแสดงเป็น form ของ OAuth2 password flow ไม่ใช่ช่อง paste bearer token ช่องเดียว

ดังนั้นปกติให้ใส่:

- `username`
- `password`

และปล่อยว่าง:

- `client_id`
- `client_secret`

จากนั้น Swagger จะไปขอ token และแนบ bearer token ให้เอง

## ทำไมไม่เห็นช่อง `Bearer <token>` ตรง ๆ

เพราะ docs UI ของโปรเจกต์นี้ผูกกับ OAuth2 password flow ของ FastAPI

ดังนั้น behavior ที่เห็นว่า Swagger ขอ:

- username
- password

ถือว่าเป็นเรื่องปกติ ไม่ใช่การตั้งค่าผิด

ถ้าคุณอยากใช้ token แบบ copy/paste เอง ก็ยังทำได้ผ่าน client อื่น เช่น:

- curl
- Postman
- Insomnia

โดยเรียก `POST /api/v1/auth/login` ก่อนแล้วค่อย copy `access_token`

## flow แนะนำหลัง bootstrap admin

ถ้าเพิ่ง bootstrap admin แล้วอยากเช็กเร็ว ๆ ว่าระบบพร้อม:

1. `GET /api/v1/auth/me`
2. `GET /api/v1/billing/me/summary`
3. `GET /api/v1/billing/me/balance/item_create`
4. `POST /api/v1/items/`
5. `GET /api/v1/billing/me/usage`
6. `GET /api/v1/billing/me/usage/report`

flow นี้ช่วยเช็กครบทั้ง:

- auth
- self-service billing
- items quota example
- usage history/report

## ถ้าลองแล้วเจอปัญหาที่พบบ่อย

### 1. กด `Authorize` แล้วงงว่าต้องใส่อะไร

ให้ใส่แค่:

- username
- password

ถ้าไม่มี user ให้ bootstrap admin ก่อน

### 2. เรียก protected route แล้วได้ `401`

เช็ก:

- login ผ่านหรือยัง
- token หมดอายุหรือยัง
- กด `Authorize` สำเร็จไหม

### 3. เรียก `POST /api/v1/items/` แล้วได้ `403`

เป็นไปได้ว่า account ยังไม่มี entitlement `item_create`

ให้เช็ก:

- `GET /api/v1/billing/me/balance/item_create`
- หรือ `GET /api/v1/billing/me/summary`

### 4. เห็น docs แต่ไม่เห็น route บางตัว

อาจเป็นเพราะ:

- feature ถูกปิดไว้ เช่น example module
- route ถูกป้องกันด้วย role แต่ยังไม่ได้ auth
- environment/config ต่างจากที่คาด

## ข้อควรระวังใน production

docs UI มีประโยชน์มากใน local/dev แต่ production ควรคิดเรื่อง exposure ให้ดี

แนวทางที่แนะนำ:

- เปิด docs เฉพาะ internal/staging ถ้าเป็นไปได้
- ป้องกัน docs ด้วย auth หรือ network controls
- อย่า expose OpenAPI public โดยไม่ตั้งใจ

## สรุป

OpenAPI/Swagger ในโปรเจกต์นี้ควรใช้เป็น:

- เครื่องมือสำรวจ API
- เครื่องมือ smoke test local
- จุดเช็ก contracts ระหว่างพัฒนา

แต่ไม่ควรถูกมองเป็น replacement ของ client-side integration tests หรือ production monitoring

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/openapi.md](/Users/pluto/Documents/git/fastapi101/docs/openapi.md)
