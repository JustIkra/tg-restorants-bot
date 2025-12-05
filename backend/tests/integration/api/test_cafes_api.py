"""Integration tests for Cafes API."""

import pytest


@pytest.mark.asyncio
async def test_get_cafes_list(client, test_cafe):
    """Test getting list of cafes (public endpoint)."""
    response = await client.get("/api/v1/cafes")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == test_cafe.id
    assert data[0]["name"] == test_cafe.name


@pytest.mark.asyncio
async def test_get_cafe_by_id(client, test_cafe):
    """Test getting cafe by ID."""
    response = await client.get(f"/api/v1/cafes/{test_cafe.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_cafe.id
    assert data["name"] == "Test Cafe"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_cafe_manager(client, manager_auth_headers):
    """Test manager can create cafe."""
    cafe_data = {
        "name": "New Cafe",
        "description": "A new test cafe",
        "is_active": True,
    }

    response = await client.post(
        "/api/v1/cafes", headers=manager_auth_headers, json=cafe_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Cafe"
    assert data["description"] == "A new test cafe"


@pytest.mark.asyncio
async def test_create_cafe_user_forbidden(client, auth_headers):
    """Test regular user cannot create cafe."""
    cafe_data = {
        "name": "Hacker Cafe",
        "description": "Unauthorized",
    }

    response = await client.post("/api/v1/cafes", headers=auth_headers, json=cafe_data)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_cafe_manager(client, manager_auth_headers, test_cafe):
    """Test manager can update cafe."""
    update_data = {
        "name": "Updated Cafe Name",
        "description": "Updated description",
    }

    response = await client.patch(
        f"/api/v1/cafes/{test_cafe.id}", headers=manager_auth_headers, json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Cafe Name"


@pytest.mark.asyncio
async def test_update_cafe_status_manager(client, manager_auth_headers, test_cafe):
    """Test manager can update cafe status."""
    update_data = {"is_active": False}

    response = await client.patch(
        f"/api/v1/cafes/{test_cafe.id}/status",
        headers=manager_auth_headers,
        json=update_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_cafe_manager(client, manager_auth_headers, test_cafe):
    """Test manager can delete cafe."""
    response = await client.delete(
        f"/api/v1/cafes/{test_cafe.id}", headers=manager_auth_headers
    )

    assert response.status_code == 204
