"""Integration tests for User Access Requests API."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest


def generate_telegram_init_data(user_data: dict, bot_token: str) -> str:
    """Generate valid Telegram WebApp initData."""
    auth_date = int(time.time())

    data = {
        "auth_date": str(auth_date),
        "user": json.dumps(user_data),
    }

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    data["hash"] = calculated_hash
    return urlencode(data)


@pytest.mark.asyncio
async def test_list_user_requests_empty(client, manager_auth_headers):
    """Test GET /user-requests returns empty list when no requests exist."""
    response = await client.get("/api/v1/user-requests", headers=manager_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_user_requests_with_data(client, manager_auth_headers):
    """Test GET /user-requests returns list of requests."""
    # Create access request by attempting auth with new user
    user_data = {
        "id": 999888777,
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
    }
    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )

    # This should create a pending request
    await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office A"},
    )

    # Now fetch requests
    response = await client.get("/api/v1/user-requests", headers=manager_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert data["items"][0]["tgid"] == 999888777
    assert data["items"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_list_user_requests_filter_by_status(client, manager_auth_headers):
    """Test filtering requests by status."""
    # Create access request
    user_data = {
        "id": 888777666,
        "first_name": "Jane",
        "last_name": "Smith",
    }
    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )
    await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office B"},
    )

    # Get pending requests
    response = await client.get(
        "/api/v1/user-requests?status=pending", headers=manager_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    # Should have at least the request we just created
    pending_requests = [r for r in data["items"] if r["tgid"] == 888777666]
    assert len(pending_requests) >= 1
    assert pending_requests[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_approve_user_request_success(client, manager_auth_headers):
    """Test POST /user-requests/{id}/approve creates user."""
    # Create access request
    user_data = {
        "id": 777666555,
        "first_name": "Bob",
        "last_name": "Johnson",
        "username": "bobjohnson",
    }
    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )
    await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office C"},
    )

    # Get request ID
    response = await client.get("/api/v1/user-requests", headers=manager_auth_headers)
    requests = response.json()["items"]
    request_item = next(r for r in requests if r["tgid"] == 777666555)
    request_id = request_item["id"]

    # Approve request
    response = await client.post(
        f"/api/v1/user-requests/{request_id}/approve",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["processed_at"] is not None

    # Verify user can now authenticate
    response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office C"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_approve_already_processed_request_fails(client, manager_auth_headers):
    """Test cannot approve already processed request."""
    # Create and approve request
    user_data = {
        "id": 666555444,
        "first_name": "Alice",
        "last_name": "Brown",
    }
    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )
    await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office D"},
    )

    # Get request ID and approve
    response = await client.get("/api/v1/user-requests", headers=manager_auth_headers)
    requests = response.json()["items"]
    request_item = next(r for r in requests if r["tgid"] == 666555444)
    request_id = request_item["id"]

    await client.post(
        f"/api/v1/user-requests/{request_id}/approve",
        headers=manager_auth_headers,
    )

    # Try to approve again
    response = await client.post(
        f"/api/v1/user-requests/{request_id}/approve",
        headers=manager_auth_headers,
    )

    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "already" in detail and ("processed" in detail or "approved" in detail)


@pytest.mark.asyncio
async def test_reject_user_request_success(client, manager_auth_headers):
    """Test POST /user-requests/{id}/reject changes status."""
    # Create access request
    user_data = {
        "id": 555444333,
        "first_name": "Charlie",
        "last_name": "Davis",
    }
    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )
    await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office E"},
    )

    # Get request ID
    response = await client.get("/api/v1/user-requests", headers=manager_auth_headers)
    requests = response.json()["items"]
    request_item = next(r for r in requests if r["tgid"] == 555444333)
    request_id = request_item["id"]

    # Reject request
    response = await client.post(
        f"/api/v1/user-requests/{request_id}/reject",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["processed_at"] is not None

    # Verify user cannot authenticate
    response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office E"},
    )

    assert response.status_code == 403
    assert "rejected" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_requests_require_manager_role(client, auth_headers):
    """Test regular user cannot view user requests."""
    response = await client.get("/api/v1/user-requests", headers=auth_headers)

    assert response.status_code == 403
