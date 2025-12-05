"""Integration tests for Users API."""

import pytest


@pytest.mark.asyncio
async def test_get_users_list_manager(client, manager_auth_headers, test_user):
    """Test manager can get list of users."""
    response = await client.get("/api/v1/users", headers=manager_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_users_list_user_forbidden(client, auth_headers):
    """Test regular user cannot get users list."""
    response = await client.get("/api/v1/users", headers=auth_headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_by_tgid(client, auth_headers, test_user):
    """Test getting user by tgid."""
    response = await client.get(f"/api/v1/users/{test_user.tgid}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["tgid"] == test_user.tgid
    assert data["name"] == test_user.name
    assert data["office"] == test_user.office


@pytest.mark.asyncio
async def test_create_user_manager(client, manager_auth_headers):
    """Test manager can create user."""
    user_data = {
        "tgid": 555666777,
        "name": "New User",
        "office": "Office C",
        "role": "user",
    }

    response = await client.post(
        "/api/v1/users", headers=manager_auth_headers, json=user_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["tgid"] == 555666777
    assert data["name"] == "New User"


@pytest.mark.asyncio
async def test_create_user_non_manager_forbidden(client, auth_headers):
    """Test regular user cannot create users."""
    user_data = {
        "tgid": 888999000,
        "name": "Hacker User",
        "office": "Office D",
    }

    response = await client.post("/api/v1/users", headers=auth_headers, json=user_data)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_manager(client, manager_auth_headers, test_user):
    """Test manager can delete user."""
    response = await client.delete(
        f"/api/v1/users/{test_user.tgid}", headers=manager_auth_headers
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_update_user_access_manager(client, manager_auth_headers, test_user):
    """Test manager can update user access."""
    update_data = {"is_active": False}

    response = await client.patch(
        f"/api/v1/users/{test_user.tgid}/access",
        headers=manager_auth_headers,
        json=update_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_get_user_balance(client, auth_headers, test_user):
    """Test getting user balance."""
    response = await client.get(
        f"/api/v1/users/{test_user.tgid}/balance", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "current_week_spent" in data
    assert "weekly_limit" in data


@pytest.mark.asyncio
async def test_update_balance_limit_manager(client, manager_auth_headers, test_user):
    """Test manager can update balance limit."""
    update_data = {"weekly_limit": 2000.00}

    response = await client.patch(
        f"/api/v1/users/{test_user.tgid}/balance/limit",
        headers=manager_auth_headers,
        json=update_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert float(data["weekly_limit"]) == 2000.00
