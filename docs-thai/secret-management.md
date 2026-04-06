# Secret Management

ไฟล์นี้อธิบายว่าอะไรควรถูกมองเป็น secret, ควรเก็บไว้ที่ไหน, และควร rotate ยังไงใน template นี้

## หลักคิดสำคัญ

แยกให้ชัดระหว่าง:

- config ปกติ
- config ที่ขึ้นกับ environment
- real secrets

template นี้รองรับ `.env` สำหรับ local ได้ดี แต่ production ไม่ควรใช้ `.env` เป็น source of truth ระยะยาว

ถ้าต้องการจุดเริ่มต้นสำหรับ production-oriented env ให้ดู [/.env.prod.example](/Users/pluto/Documents/git/fastapi101/.env.prod.example) ใช้เป็น inventory/checklist ได้ แต่ไม่ควร treat เป็นที่เก็บ real secrets ระยะยาว

## อะไรควรถูกมองเป็น secret

ตัวอย่างหลัก:

- `SECURITY__SECRET_KEY`
- `DATABASE__URL` ถ้ามี credentials
- Redis URLs ที่มี credentials
- broker URLs ที่มี credentials
- `METRICS__AUTH_TOKEN`
- email provider credentials
- webhook auth tokens / webhook URLs

ส่วนที่มักเป็น config ปกติ ไม่ใช่ secret เช่น:

- `APP__NAME`
- `APP__ENV`
- `API__V1_PREFIX`
- `API__CORS_ORIGINS`
- password policy thresholds
- logging / health / telemetry toggles

## ควรเก็บ secret ไว้ที่ไหน

### Local development

รับได้ถ้า:

- copy `.env.example` หรือ `.env.min.example`
- ใช้ local/fake credentials
- ไม่ reuse production credentials

### Shared dev / staging

แนะนำให้:

- เก็บ non-secret defaults ใน manifests/ConfigMaps
- ดึง real secrets จาก platform secret store
- ไม่ commit long-lived shared secrets ลง repo

### Production

แนะนำให้:

- ใช้ secret manager เช่น Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault หรือ Kubernetes Secrets ที่อยู่ภายใต้ platform controls
- inject ตอน runtime
- audit ได้ว่าใครอ่านหรือเปลี่ยน secret ได้

## Suggested secret inventory

อย่างน้อยควรมี inventory ที่ตอบได้ว่า:

- secret ตัวนี้คืออะไร
- owner คือใคร
- rotate priority เท่าไร
- กระทบ workload ไหนบ้าง

ตัวอย่างขั้นต่ำ:

- JWT signing secret
- DB credentials
- Redis credentials
- broker credentials
- metrics auth token
- email/webhook provider credentials

## Rotation ที่ควรมี

อย่างน้อยควรมี runbook สำหรับ:

- `SECURITY__SECRET_KEY`
- DB credentials
- Redis/broker credentials
- provider API keys
- metrics auth token

เวลาหมุน secret ควรตอบให้ได้ว่า:

- อะไรต้อง restart
- อะไรต้อง roll deployment
- มี backward-compatible overlap period ไหม
- ถ้าพังจะ rollback ยังไง

## Rotation principles

แนวคิดที่แนะนำ:

- หมุนทีละ secret class
- รู้ก่อนว่า workload ไหนใช้ secret นี้
- ตรวจ health/auth/worker หลัง rotation
- อย่าหมุนด้วยการแก้ค่าใน pod/container แบบ manual

## ตัวอย่าง runbook ย่อ

### JWT signing secret

ผลกระทบ:

- access/refresh tokens เดิมอาจใช้ไม่ได้ทันที

ดังนั้นควร:

1. ประกาศ maintenance window หรือ forced re-auth
2. generate secret ใหม่
3. update secret store
4. roll app และ services ที่ verify JWT นี้
5. เช็ก login / refresh / protected routes
6. monitor `401` และ `auth.invalid_token`

### DB credentials

1. ออก credentials ใหม่ก่อน
2. update secret store
3. roll API, worker, dispatcher, jobs
4. เช็ก `/health/ready`, migrations, worker publishing
5. ลบ credentials เก่าหลังทุก workload ใช้ค่าชุดใหม่แล้ว

### Redis / broker credentials

1. issue credentials ใหม่
2. update secret source
3. rollทุก workload ที่ใช้ connection นี้
4. เช็ก rate limiting / cache / queue publishing / worker consumption
5. ลบ credentials เก่าหลังระบบนิ่ง

### Email / webhook provider credentials

1. create replacement credential
2. update secret source
3. roll workloads ที่ส่ง event ชนิดนั้น
4. trigger controlled test message/webhook
5. เช็ก provider dashboard และ app logs
6. revoke credential เก่า

## Checklist หลัง rotate

อย่างน้อยควรเช็ก:

- `/health/live`
- `/health/ready`
- login
- refresh token flow
- protected endpoint 1 ตัว
- worker publishing/consumption ถ้าเปิด worker
- outbox dispatcher ถ้าเปิด outbox
- email/webhook delivery ถ้า secret ที่เปลี่ยนเกี่ยวข้องกับ provider

และดู metrics เพิ่ม:

- error rate
- readiness failures
- auth failures
- queue backlog / DLQ depth

## backup / restore / rollback story

production readiness ไม่ได้มีแค่เรื่อง secret rotation ยังต้องตอบให้ได้ด้วยว่า:

- backup อะไรบ้าง
- ซ้อม restore หรือยัง
- rollback release ทำยังไง
- restore data ต่างจาก rollback app ยังไง

### scope ของ backup

อย่างน้อยควรคิดถึง:

- Postgres
- Redis ถ้าเก็บ state ที่ยอมเสียไม่ได้
- broker state ถ้า operational model ของคุณพึ่ง durable queues
- config metadata และ secret inventory

baseline ที่แนะนำสำหรับ template นี้:

- Postgres backup เป็นสิ่งที่ต้องมี
- Redis backup เป็น optional ถ้า Redis ใช้แค่ cache
- ถ้า Redis ใช้กับ shared rate limiting หรือ idempotency และคุณแคร์ continuity ของ state มากขึ้น ค่อยยกระดับ persistence policy
- broker durability ควรจัดการที่ platform/broker layer ไม่ใช่คิดว่าแอปจะจัดการแทน

### สิ่งที่ควรตอบให้ได้สำหรับ Postgres

- backup บ่อยแค่ไหน
- retention เท่าไร
- เก็บที่ไหน
- เข้ารหัสหรือไม่
- ใครเป็น owner ตอน restore
- ล่าสุดซ้อม restore เมื่อไร

แนวที่แนะนำ:

- ถ้าใช้ managed Postgres ให้ใช้ backup/PITR ของ platform เป็น baseline
- มีวิธี restore เข้า environment แยกเพื่อ validate ได้

### การซ้อม restore

backup ที่ไม่เคยถูก restore จริง ยังไม่น่าไว้ใจพอ

อย่างน้อยควรซ้อม:

1. restore Postgres backup เข้า environment แยก
2. ชี้ app copy หนึ่งไปยัง DB ที่ restore แล้ว
3. เช็ก login, protected route, และ business flow ตัวแทนอย่างน้อย 1 ตัว
4. เช็ก Alembic version state ให้ตรงตามที่คาด

### rollback vs restore

ให้แยกสองคำนี้ออกจากกัน:

- rollback:
  ย้อน app release ไป version ก่อนหน้า
- restore:
  กู้ data หรือ infra state จาก backup

ใช้ rollback ก่อนเมื่อ:

- image ใหม่พัง
- worker build ใหม่พัง
- migration ยัง forward-compatible กับ app version ก่อนหน้า

ใช้ restore เมื่อ:

- data ถูกลบหรือเสียหาย
- migration แบบ destructive ผิดพลาด
- infrastructure failure ทำให้ต้องกู้ state

### minimum recovery runbook

ก่อนจะเรียกว่าพร้อม production จริง ควรมีคำตอบอย่างน้อย:

1. ใครมีสิทธิ์สั่ง restore
2. backup อยู่ที่ไหน
3. รับ recovery point objective ได้เท่าไร
4. รับ recovery time objective ได้เท่าไร
5. จะ validate restored environment ยังไงก่อนเปิด traffic

## Checklist ขั้นต่ำ

- ไม่ commit `.env` จริงลง repo
- ใช้ sample values เฉพาะ local
- production secrets แยกจาก example files ชัดเจน
- มี owner ของ secret แต่ละตัว
- มี cadence หรือเหตุการณ์ที่บอกว่าต้อง rotate เมื่อไหร่

## ข้อผิดพลาดที่พบบ่อย

- ใช้ local sample values ต่อใน staging/production
- เก็บ secrets ไว้ใน compose/manifests แบบ plain text
- ไม่มี owner ของ secret
- หมุน secret แล้วไม่รู้ว่ากระทบ worker / metrics / provider integrations ตรงไหนบ้าง
- หมุน JWT signing secret โดยไม่เตรียมการเรื่อง token invalidation

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/secret-management.md](/Users/pluto/Documents/git/fastapi101/docs/secret-management.md)
