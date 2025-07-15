import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from database import database


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_db():
    await database.connect()
    yield
    await database.disconnect()


@pytest_asyncio.fixture(scope="module")
async def test_client():
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(scope="module")
async def create_test_user(test_client):
    response = await test_client.post("/users/", json={
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200 or response.status_code == 400  # 400 if already exists


@pytest_asyncio.fixture(scope="module")
async def auth_token(test_client, create_test_user):
    response = await test_client.post("/token", data={
        "username": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_user(test_client):
    response = await test_client.post("/users/", json={
        "email": "testuser2@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200 or response.status_code == 400


@pytest.mark.asyncio
async def test_add_to_cart_requires_auth(test_client):
    response = await test_client.post("/cart/", json={
        "product_id": 1,
        "quantity": 2
    })
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_add_to_cart_with_auth(test_client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await test_client.post("/cart/", json={
        "product_id": 1,
        "quantity": 2
    }, headers=headers)
    assert response.status_code in [200, 404]  
