import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from database import database



# # Ensure current directory is in path
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ✅ Correct fixture setup for async DB handling
@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_and_teardown_db():
    await database.connect()
    yield
    await database.disconnect()


# ✅ Create user test
@pytest.mark.asyncio
async def test_create_user():
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/users/", json={
            "email": "testuser@example.com",
            "password": "testpassword"
        })
        assert response.status_code in [200, 400]


# ✅ Token fixture for reuse
@pytest_asyncio.fixture(scope="module")
async def auth_token():
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/token", data={
            "username": "testuser@example.com",
            "password": "testpassword"
        })
        assert response.status_code == 200
        return response.json()["access_token"]


# ✅ Unauthorized cart add
@pytest.mark.asyncio
async def test_add_to_cart_requires_auth():
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/cart/", json={
            "product_id": 1,
            "quantity": 2
        })
        assert response.status_code == 401


# ✅ Authorized cart add
@pytest.mark.asyncio
async def test_add_to_cart_with_auth(auth_token):
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        response = await client.post("/cart/", json={
            "product_id": 1,
            "quantity": 2
        })
        assert response.status_code in [200, 404]  # Passes if product not found

