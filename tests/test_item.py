# tests/test_items.py
import pytest

@pytest.mark.asyncio
async def test_create_item(client, token_headers):
    # 1. ทดสอบสร้าง Item (ต้องส่ง headers ไปด้วย)
    payload = {"title": "Test Item", "description": "This is a test"}
    response = await client.post(
        "/api/v1/items/", 
        json=payload, 
        headers=token_headers # <--- ใส่ Token ตรงนี้
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Item"
    assert "id" in data
    assert data["owner_id"] is not None

@pytest.mark.asyncio
async def test_create_item_unauthorized(client):
    # 2. ทดสอบกรณีไม่ส่ง Token (ต้องได้ 401)
    payload = {"title": "No Token"}
    response = await client.post("/api/v1/items/", json=payload)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_read_items(client, token_headers):
    # 3. ทดสอบดึงรายการ Items
    response = await client.get("/api/v1/items/", headers=token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_read_items_invalid_token(client):
    headers = {"Authorization": "Bearer not-a-real-token"}
    response = await client.get("/api/v1/items/", headers=headers)
    assert response.status_code == 401