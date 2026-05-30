# เอกสารภาษาไทย

โฟลเดอร์นี้เป็นชุดเอกสารภาษาไทยสำหรับทีมที่ต้องการเริ่มใช้ template นี้โดยไม่ต้องไล่อ่าน docs ภาษาอังกฤษทั้งหมดตั้งแต่ต้น

แนวทางของชุดนี้คือ:

- อธิบายภาพรวมให้เข้าใจก่อน
- ช่วย onboarding ทีมใหม่เร็วขึ้น
- ชี้ลำดับการอ่านที่เหมาะกับการเริ่มโปรเจกต์
- ให้เอกสารไทยใช้ได้จริงมากขึ้นทั้งฝั่ง backend, client, และ ops
- ลิงก์กลับไป docs ภาษาอังกฤษเมื่อเป็นเรื่อง reference เชิงลึก

หมายเหตุ:

- เอกสารภาษาอังกฤษใน [docs](../docs) ยังเป็น reference หลักของระบบ
- เอกสารใน `docs-thai` ตอนนี้ถูกขยายให้ใช้เป็น onboarding/reference ภาษาไทยได้จริงมากขึ้น ไม่ได้เป็นแค่ลิงก์กลับไปอังกฤษอย่างเดียว
- ถ้าคุณเพิ่งเริ่มกับ repo นี้ ให้ใช้ไฟล์นี้เป็นจุดตั้งต้นก่อน

## เริ่มอ่านจากตรงไหนดี

ถ้าคุณเพิ่ง clone โปรเจกต์นี้:

1. อ่าน [bootstrap.md](../docs-thai/bootstrap.md)
2. อ่าน [development.md](../docs-thai/development.md)
3. อ่าน [platform-starter.md](../docs-thai/platform-starter.md)
4. อ่าน [architecture.md](../docs-thai/architecture.md)
5. อ่าน [database-schema.md](../docs-thai/database-schema.md) ถ้าจะเข้าใจตารางและความสัมพันธ์หลัก
6. อ่าน [database-migrations.md](../docs-thai/database-migrations.md) ถ้าจะเปลี่ยน schema หรือ debug ปัญหา DB ใน local
7. ถ้าจะปรับ config อ่าน [configuration.md](../docs-thai/configuration.md)
8. ถ้าจะ deploy ต่อ อ่าน [deployment.md](../docs-thai/deployment.md)
9. ถ้าจะ deploy แบบ production-minded ต่อ อ่าน [production-topology.md](../docs-thai/production-topology.md), [observability.md](../docs-thai/observability.md), และ [first-deploy-checklist.md](../docs-thai/first-deploy-checklist.md)
10. ก่อน deploy shared env จริง ให้อ่าน [security-hardening.md](../docs-thai/security-hardening.md) ควบคู่กับ [security.md](../docs-thai/security.md)
11. ถ้า service เริ่มโต อ่าน [operations.md](../docs-thai/operations.md) และ [security.md](../docs-thai/security.md)

ถ้าต้องการเวอร์ชันย่อมาก ๆ:

- เริ่มจาก [bootstrap.md](../docs-thai/bootstrap.md)
- ต่อด้วย [development.md](../docs-thai/development.md)
- แล้วค่อยเลือกอ่านตามบทบาทของตัวเอง

## เอกสารในชุดนี้

- [adoption-checklists.md](../docs-thai/adoption-checklists.md): checklist การ adopt template และตัวช่วยเลือก feature
- [api-contracts.md](../docs-thai/api-contracts.md): สรุป response/error contract ของ API
- [api-guide.md](../docs-thai/api-guide.md): วิธีเพิ่ม endpoint และ resource ใหม่
- [api-recipes.md](../docs-thai/api-recipes.md): ตัวอย่าง flow การเรียก API แบบใช้งานจริง
- [bootstrap.md](../docs-thai/bootstrap.md): ขั้นตอนเริ่มโปรเจกต์ใหม่แบบ day-0/day-1
- [development.md](../docs-thai/development.md): วิธีรัน local, test, และ workflow ตอนพัฒนา
- [architecture.md](../docs-thai/architecture.md): อธิบายโครงสร้างและการไหลของงานในระบบ
- [database-schema.md](../docs-thai/database-schema.md): แผนผัง schema และความสัมพันธ์ของ tables หลักในระบบ
- [database-migrations.md](../docs-thai/database-migrations.md): ขั้นตอนการแก้ schema, สร้าง migration, และ debug ปัญหา DB ใน local
- [auth-for-clients.md](../docs-thai/auth-for-clients.md): คู่มือ auth จากมุมของคนใช้ API
- [configuration.md](../docs-thai/configuration.md): อธิบายกลุ่ม config ที่ควรรู้ก่อนเริ่ม
- [deployment.md](../docs-thai/deployment.md): แนวทางขึ้นระบบ, health checks, metrics, และ deployment mindset
- [/.env.prod.example](../.env.prod.example): baseline env example สำหรับ production-oriented config review
- [production-topology.md](../docs-thai/production-topology.md): topology ที่แนะนำสำหรับ production-like / production deployment
- [observability.md](../docs-thai/observability.md): baseline observability ที่ควรเปิดเมื่อจะใช้จริง
- [first-deploy-checklist.md](../docs-thai/first-deploy-checklist.md): checklist ก่อน deploy ครั้งแรก
- [error-codes.md](../docs-thai/error-codes.md): สรุป error codes ที่สำคัญ
- [load-testing.md](../docs-thai/load-testing.md): แนวคิดและ workflow สำหรับทดสอบโหลด
- [openapi.md](../docs-thai/openapi.md): วิธีใช้ OpenAPI / Swagger UI
- [operations.md](../docs-thai/operations.md): runbook และงานดูแลระบบ
- [platform-starter.md](../docs-thai/platform-starter.md): อธิบายแนวคิด Core / Extensions / Advanced
- [secret-management.md](../docs-thai/secret-management.md): แนวทางจัดการ secrets และการ rotate
- [security.md](../docs-thai/security.md): ภาพรวม security baseline ของ template
- [security-hardening.md](../docs-thai/security-hardening.md): checklist รอบแรกสำหรับปิด unsafe defaults และ review sensitive surfaces ก่อนขึ้น shared env
- [versioning.md](../docs-thai/versioning.md): วิธีคิดเรื่อง version ของ template
- [release-notes.md](../docs-thai/release-notes.md): release notes ของ stable template baseline และ action items สำหรับ adopter

## สถานะความครอบคลุมของ docs-thai

ตอนนี้เอกสารไทยแบ่งความพร้อมใช้งานได้ประมาณนี้

### พร้อมใช้เป็น Thai-first reference ได้เลย

- [bootstrap.md](../docs-thai/bootstrap.md)
- [development.md](../docs-thai/development.md)
- [platform-starter.md](../docs-thai/platform-starter.md)
- [architecture.md](../docs-thai/architecture.md)
- [database-schema.md](../docs-thai/database-schema.md)
- [database-migrations.md](../docs-thai/database-migrations.md)
- [configuration.md](../docs-thai/configuration.md)
- [deployment.md](../docs-thai/deployment.md)
- [production-topology.md](../docs-thai/production-topology.md)
- [observability.md](../docs-thai/observability.md)
- [first-deploy-checklist.md](../docs-thai/first-deploy-checklist.md)
- [security.md](../docs-thai/security.md)
- [operations.md](../docs-thai/operations.md)
- [auth-for-clients.md](../docs-thai/auth-for-clients.md)
- [api-recipes.md](../docs-thai/api-recipes.md)
- [openapi.md](../docs-thai/openapi.md)
- [api-contracts.md](../docs-thai/api-contracts.md)

### พร้อมใช้ได้ดี แต่ยังเหมาะกับการเปิดอังกฤษประกบเมื่อจะลงลึกมาก

- [adoption-checklists.md](../docs-thai/adoption-checklists.md)
- [api-guide.md](../docs-thai/api-guide.md)
- [load-testing.md](../docs-thai/load-testing.md)
- [secret-management.md](../docs-thai/secret-management.md)
- [error-codes.md](../docs-thai/error-codes.md)
- [versioning.md](../docs-thai/versioning.md)

### companion docs / draft

- [billing-entitlements-draft.md](../docs-thai/billing-entitlements-draft.md)

แนวคิดของหมวดนี้คือ:

- ถ้าเป็น onboarding, day-0/day-1, หรือการใช้งานปกติ ให้อ่านฝั่งไทยได้เลย
- ถ้ากำลังจะ implement subsystem ใหม่เชิงลึก หรือเทียบ behavior ระดับละเอียดมาก ให้เปิด docs อังกฤษประกบด้วย

สรุปสั้น ๆ:

- ถ้าจะ “เริ่มใช้” อ่านไทยได้ก่อน
- ถ้าจะ “ออกแบบหรือขยายระบบ” เปิดอังกฤษประกบด้วยจะดีที่สุด

## ถ้าอยากอ่านตามบทบาท

ถ้าคุณเป็น backend developer:

1. [development.md](../docs-thai/development.md)
2. [api-guide.md](../docs-thai/api-guide.md)
3. [architecture.md](../docs-thai/architecture.md)
4. [database-schema.md](../docs-thai/database-schema.md)
5. [database-migrations.md](../docs-thai/database-migrations.md)
6. [api-contracts.md](../docs-thai/api-contracts.md)

ถ้าคุณเป็น frontend/mobile/client developer:

1. [auth-for-clients.md](../docs-thai/auth-for-clients.md)
2. [api-recipes.md](../docs-thai/api-recipes.md)
3. [openapi.md](../docs-thai/openapi.md)

ถ้าคุณเป็น ops/platform engineer:

1. [deployment.md](../docs-thai/deployment.md)
2. [production-topology.md](../docs-thai/production-topology.md)
3. [observability.md](../docs-thai/observability.md)
4. [first-deploy-checklist.md](../docs-thai/first-deploy-checklist.md)
5. [operations.md](../docs-thai/operations.md)
6. [secret-management.md](../docs-thai/secret-management.md)
7. [database-migrations.md](../docs-thai/database-migrations.md)
8. [load-testing.md](../docs-thai/load-testing.md)

ถ้าคุณเป็นคนเริ่มโปรเจกต์/tech lead:

1. [platform-starter.md](../docs-thai/platform-starter.md)
2. [adoption-checklists.md](../docs-thai/adoption-checklists.md)
3. [configuration.md](../docs-thai/configuration.md)
4. [security.md](../docs-thai/security.md)

## ถ้าอยากดู reference เชิงลึก

ให้กลับไปที่ชุด docs ภาษาอังกฤษ:

- [docs/platform-starter.md](../docs/platform-starter.md)
- [docs/configuration.md](../docs/configuration.md)
- [docs/security.md](../docs/security.md)
- [docs/deployment.md](../docs/deployment.md)
- [docs/operations.md](../docs/operations.md)
