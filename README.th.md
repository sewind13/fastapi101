# FastAPI Product Template (ภาษาไทย)

repo นี้คือ FastAPI starter ที่ตั้งใจทำสำหรับการเริ่มโปรเจกต์จริง ไม่ใช่แค่ demo app หรือ CRUD boilerplate เบา ๆ

สิ่งที่มีให้ตั้งแต่ต้น เช่น:

- versioned API routing
- config ผ่าน `BaseSettings`
- Postgres + Alembic migrations
- service/repository separation
- JWT auth + refresh rotation
- logging, health, และ metrics baseline
- worker / outbox / DLQ tooling แบบ optional
- billing / entitlement example แบบ account-based
- docs อังกฤษและไทย

แนวคิดของ template นี้คือ:

- ให้ทีมเริ่มจากฐานที่แข็ง
- เปิด feature เพิ่มเมื่อ product ต้องใช้จริง
- ไม่บังคับให้ทุก service ต้องแบก subsystem ทุกตัวตั้งแต่วันแรก

## เริ่มเร็วที่สุด

```bash
cp .env.min.example .env
make up
make ps
```

ถ้าจะสร้าง admin คนแรก:

```bash
export BOOTSTRAP_ADMIN_PASSWORD='replace-with-a-strong-secret'
make bootstrap-admin-in-container-env args="--username admin --email admin@example.com --role platform_admin"
```

## ถัดไปควรอ่านอะไร

เริ่มจากชุดเอกสารภาษาไทยที่ [docs-thai/README.md](/Users/pluto/Documents/git/fastapi101/docs-thai/README.md) ซึ่งเป็น index หลักของ docs ไทย

ลำดับแนะนำ:

1. [docs-thai/bootstrap.md](/Users/pluto/Documents/git/fastapi101/docs-thai/bootstrap.md)
2. [docs-thai/development.md](/Users/pluto/Documents/git/fastapi101/docs-thai/development.md)
3. [docs-thai/platform-starter.md](/Users/pluto/Documents/git/fastapi101/docs-thai/platform-starter.md)
4. [docs-thai/architecture.md](/Users/pluto/Documents/git/fastapi101/docs-thai/architecture.md)
5. [docs-thai/database-schema.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-schema.md)
6. [docs-thai/database-migrations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-migrations.md)
7. [docs-thai/configuration.md](/Users/pluto/Documents/git/fastapi101/docs-thai/configuration.md)

ถ้าอยากเห็นภาพรวม database แบบเร็วที่สุด ให้เปิด ERD ใน [docs-thai/database-schema.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-schema.md) ก่อน

## ถ้าอยากดูตามบทบาท

ถ้าคุณเป็น backend developer:

- [docs-thai/api-guide.md](/Users/pluto/Documents/git/fastapi101/docs-thai/api-guide.md)
- [docs-thai/architecture.md](/Users/pluto/Documents/git/fastapi101/docs-thai/architecture.md)
- [docs-thai/database-schema.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-schema.md)
- [docs-thai/database-migrations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-migrations.md)

ถ้าคุณเป็น frontend/mobile/client developer:

- [docs-thai/auth-for-clients.md](/Users/pluto/Documents/git/fastapi101/docs-thai/auth-for-clients.md)
- [docs-thai/api-recipes.md](/Users/pluto/Documents/git/fastapi101/docs-thai/api-recipes.md)
- [docs-thai/openapi.md](/Users/pluto/Documents/git/fastapi101/docs-thai/openapi.md)

ถ้าคุณเป็น ops/platform engineer:

- [docs-thai/deployment.md](/Users/pluto/Documents/git/fastapi101/docs-thai/deployment.md)
- [docs-thai/operations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/operations.md)
- [docs-thai/security.md](/Users/pluto/Documents/git/fastapi101/docs-thai/security.md)
- [docs-thai/secret-management.md](/Users/pluto/Documents/git/fastapi101/docs-thai/secret-management.md)
- [docs-thai/database-migrations.md](/Users/pluto/Documents/git/fastapi101/docs-thai/database-migrations.md)

## หมายเหตุ

- docs อังกฤษยังเป็น reference หลักที่ละเอียดที่สุด
- แต่ `docs-thai` ตอนนี้ถูกขยายให้ใช้เป็น onboarding/reference ภาษาไทยได้จริงมากขึ้นแล้ว
- ถ้าจะเริ่มงานใหม่ day-0/day-1 ให้อ่านฝั่งไทยก่อนได้เลย
- ถ้าจะลงลึก implementation หรือเทียบ behavior รายละเอียดมาก ๆ ค่อยเปิด docs อังกฤษประกบ

ดู README อังกฤษได้ที่ [README.md](/Users/pluto/Documents/git/fastapi101/README.md)
