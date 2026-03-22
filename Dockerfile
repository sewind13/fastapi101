# 1. ใช้ Python Image ตัวเล็กและเร็ว (Alpine/Slim)
FROM python:3.13-slim

# 2. ตั้งค่า Working Directory ในคอนเทนเนอร์
WORKDIR /app

# 3. ป้องกัน Python สร้างไฟล์ .pyc และให้ Log แสดงผลทันที
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. ติดตั้ง dependencies สำหรับ psycopg (ถ้าใช้แบบ binary อาจไม่ต้อง แต่ใส่ไว้เพื่อความชัวร์)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 5. ติดตั้ง uv (เครื่องมือจัดการ package ที่เราใช้)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 6. Copy ไฟล์โปรเจกต์เข้าไป
COPY . .

# 7. ติดตั้ง Library ทั้งหมดผ่าน uv
RUN uv sync --frozen

# 8. สั่งรันแอป (ใช้พอร์ต 8000)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]