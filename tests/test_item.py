# tests/test_items.py
import pytest

@pytest.mark.asyncio
async def test_create_item(client):
    # ทดสอบสร้าง Item
    payload = {"title": "Test Item", "description": "This is a test"}
    response = await client.post("/api/v1/items/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Item"
    assert "id" in data

@pytest.mark.asyncio
async def test_read_item_not_found(client):
    # ทดสอบกรณีหา Item ไม่เจอ (Edge Case)
    response = await client.get("/api/v1/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "ไม่พบข้อมูลที่คุณระบุ"