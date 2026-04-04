# Versioning ของ Template

template นี้ควรมี version ของตัวมันเอง ไม่ใช่ดูแค่ version ของแอปตัวอย่าง

เหตุผลคือสิ่งที่เปลี่ยนใน repo นี้กระทบ:

- contract ของ template
- security baseline
- config names
- deployment steps
- adoption cost ของทีมที่ใช้ template นี้

## แนวทางที่แนะนำ

ใช้ semantic versioning:

- `MAJOR`
  breaking changes
- `MINOR`
  capability ใหม่ที่ยัง backward-compatible
- `PATCH`
  fixes, docs, dependency bumps, small improvements

## อะไรถือเป็น breaking change

ตัวอย่างที่ควรถือเป็น `MAJOR`:

- เปลี่ยนชื่อ env vars
- เปลี่ยน response contract แบบไม่ compatible
- ลบ routes/jobs/modules ที่ documented ไว้แล้ว
- เปลี่ยน auth/security behavior จนทีมที่ adopt ต้องแก้ code หรือ operations
- เปลี่ยน bootstrap/deployment flow แบบต้อง migrate

## release discipline ที่แนะนำ

ทุกครั้งที่ออก template release:

1. update version ใน `pyproject.toml`
2. tag release ใน git
3. เขียน release note สั้น ๆ
4. บอกชัดว่ามี adopter action items หรือไม่

## ทีมที่ใช้ template ควรทำอะไร

- บันทึกว่าตัวเองเริ่มจาก template version ไหน
- รู้ว่า security baseline ตอนเริ่มคืออะไร
- ใช้ข้อมูลนี้ตัดสินใจว่าควร backport release ใหม่หรือไม่

## ถ้ายังไม่พร้อมทำ changelog เต็ม

อย่างน้อยควรมี:

- git tag ต่อ stable release
- release note สั้น ๆ ต่อ tag
- note ใน PR เมื่อมี template-breaking change

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/versioning.md](/Users/pluto/Documents/git/fastapi101/docs/versioning.md)
