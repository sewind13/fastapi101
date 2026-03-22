#!/bin/bash

# 1. แสดงข้อความทักทายสวยๆ
echo "🚀 Starting FastAPI 101 Docker Stack..."

# 2. ตรวจสอบว่ามีไฟล์ .env หรือไม่ (ป้องกันแอปพังเพราะหา DB ไม่เจอ)
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# 3. รัน Docker Compose (รวมการ Build และล้างขยะเก่า)
# --build: บังคับ build ใหม่ถ้ามีการแก้โค้ด
# --remove-orphans: ลบคอนเทนเนอร์เก่าที่ค้างอยู่
docker compose up --build --remove-orphans