import pytest

@pytest.mark.asyncio
async def test_register_user_success(client):
    # 1. ทดสอบสมัครสมาชิกสำเร็จ
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "strongpassword123"
    }
    response = await client.post("/api/v1/users/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data  # สำคัญมาก: ต้องไม่มี Password หลุดออกมา

@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    # 2. ทดสอบสมัครด้วย Username ซ้ำ (ต้องได้ 400)
    payload = {
        "username": "sameuser",
        "email": "user1@example.com",
        "password": "password123"
    }
    await client.post("/api/v1/users/", json=payload) # สมัครครั้งแรก
    
    # สมัครครั้งที่สองด้วย username เดิม
    payload["email"] = "user2@example.com" 
    response = await client.post("/api/v1/users/", json=payload)
    
    assert response.status_code == 400
    assert "Username หรือ Email นี้ถูกใช้งานไปแล้ว" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_success(client):
    # 3. ทดสอบ Login สำเร็จเพื่อเอา Token
    # สร้าง User ไว้ก่อน
    register_payload = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "correct_password"
    }
    await client.post("/api/v1/users/", json=register_payload)
    
    # พยายาม Login
    login_data = {
        "username": "loginuser",
        "password": "correct_password"
    }
    # หมายเหตุ: OAuth2PasswordRequestForm รับข้อมูลแบบ form-data ไม่ใช่ json
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client):
    # 4. ทดสอบ Login ด้วยรหัสผ่านที่ผิด (ต้องได้ 401)
    register_payload = {
        "username": "wrongpwuser",
        "email": "wrongpw@example.com",
        "password": "real_password"
    }
    await client.post("/api/v1/users/", json=register_payload)
    
    login_data = {
        "username": "wrongpwuser",
        "password": "fake_password"
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "Username หรือ Password ไม่ถูกต้อง" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_user_not_found(client):
    response = await client.get("/api/v1/users/9999") # ID ที่ไม่มีอยู่จริง
    assert response.status_code == 404