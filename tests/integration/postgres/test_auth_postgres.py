import pytest


@pytest.mark.integration
@pytest.mark.postgres
@pytest.mark.asyncio
async def test_register_user_success_postgres(postgres_client):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "strongpassword123",
    }
    response = await postgres_client.post("/api/v1/users/", json=payload)

    assert response.status_code == 201


@pytest.mark.integration
@pytest.mark.postgres
@pytest.mark.asyncio
async def test_register_user_isolation_postgres(postgres_client):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "strongpassword123",
    }
    response = await postgres_client.post("/api/v1/users/", json=payload)

    assert response.status_code == 201
