"""Integration tests for Cafe Links API."""

import pytest

from src.models.cafe import Cafe, LinkRequestStatus


@pytest.fixture
async def unlinked_cafe(db_session):
    """Create an unlinked cafe for testing."""
    cafe = Cafe(
        name="Test Cafe for Linking",
        description="A test cafe",
        is_active=True,
        tg_chat_id=None,
        tg_username=None,
        notifications_enabled=True,
        linked_at=None,
    )
    db_session.add(cafe)
    await db_session.commit()
    await db_session.refresh(cafe)
    return cafe


async def test_create_link_request_endpoint(client, unlinked_cafe):
    """Test POST /cafes/{cafe_id}/link-request endpoint."""
    payload = {
        "tg_chat_id": 123456789,
        "tg_username": "test_cafe_bot",
    }

    response = await client.post(
        f"/api/v1/cafes/{unlinked_cafe.id}/link-request",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["cafe_id"] == unlinked_cafe.id
    assert data["tg_chat_id"] == 123456789
    assert data["tg_username"] == "test_cafe_bot"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data


async def test_create_link_request_cafe_not_found(client):
    """Test creating link request for non-existent cafe returns 404."""
    payload = {
        "tg_chat_id": 123456789,
        "tg_username": "test_cafe_bot",
    }

    response = await client.post(
        "/api/v1/cafes/99999/link-request",
        json=payload,
    )

    assert response.status_code == 404
    assert "Cafe not found" in response.json()["detail"]


async def test_create_link_request_cafe_already_linked(
    client, db_session, unlinked_cafe
):
    """Test creating link request for already linked cafe returns 400."""
    # Link the cafe
    unlinked_cafe.tg_chat_id = 987654321
    await db_session.commit()

    payload = {
        "tg_chat_id": 123456789,
        "tg_username": "test_cafe_bot",
    }

    response = await client.post(
        f"/api/v1/cafes/{unlinked_cafe.id}/link-request",
        json=payload,
    )

    assert response.status_code == 400
    assert "already linked" in response.json()["detail"]


async def test_list_requests_manager_only(
    client, unlinked_cafe, manager_auth_headers
):
    """Test GET /cafe-requests endpoint (manager only)."""
    # Create some requests first
    for i in range(3):
        await client.post(
            f"/api/v1/cafes/{unlinked_cafe.id}/link-request",
            json={
                "tg_chat_id": 123456789 + i,
                "tg_username": f"bot_{i}",
            },
        )

    # List as manager
    response = await client.get(
        "/api/v1/cafes/cafe-requests",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 3


async def test_list_requests_unauthorized(client, auth_headers):
    """Test that non-manager cannot list requests."""
    response = await client.get(
        "/api/v1/cafes/cafe-requests",
        headers=auth_headers,  # Regular user, not manager
    )

    assert response.status_code == 403


async def test_approve_request_endpoint(
    client, unlinked_cafe, manager_auth_headers, db_session
):
    """Test POST /cafe-requests/{request_id}/approve endpoint."""
    # Create request
    create_response = await client.post(
        f"/api/v1/cafes/{unlinked_cafe.id}/link-request",
        json={
            "tg_chat_id": 123456789,
            "tg_username": "test_cafe_bot",
        },
    )
    request_id = create_response.json()["id"]

    # Approve request
    response = await client.post(
        f"/api/v1/cafes/cafe-requests/{request_id}/approve",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["processed_at"] is not None

    # Verify cafe was updated
    await db_session.refresh(unlinked_cafe)
    assert unlinked_cafe.tg_chat_id == 123456789
    assert unlinked_cafe.tg_username == "test_cafe_bot"
    assert unlinked_cafe.linked_at is not None


async def test_approve_request_unauthorized(client, unlinked_cafe, auth_headers):
    """Test that non-manager cannot approve requests."""
    # Create request
    create_response = await client.post(
        f"/api/v1/cafes/{unlinked_cafe.id}/link-request",
        json={
            "tg_chat_id": 123456789,
            "tg_username": "test_cafe_bot",
        },
    )
    request_id = create_response.json()["id"]

    # Try to approve as regular user
    response = await client.post(
        f"/api/v1/cafes/cafe-requests/{request_id}/approve",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_reject_request_endpoint(
    client, unlinked_cafe, manager_auth_headers
):
    """Test POST /cafe-requests/{request_id}/reject endpoint."""
    # Create request
    create_response = await client.post(
        f"/api/v1/cafes/{unlinked_cafe.id}/link-request",
        json={
            "tg_chat_id": 123456789,
            "tg_username": "test_cafe_bot",
        },
    )
    request_id = create_response.json()["id"]

    # Reject request
    response = await client.post(
        f"/api/v1/cafes/cafe-requests/{request_id}/reject",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["processed_at"] is not None

    # Verify cafe was NOT updated
    assert unlinked_cafe.tg_chat_id is None


async def test_update_notifications_endpoint(
    client, db_session, unlinked_cafe, manager_auth_headers
):
    """Test PATCH /cafes/{cafe_id}/notifications endpoint."""
    # Link cafe first
    unlinked_cafe.tg_chat_id = 123456789
    unlinked_cafe.notifications_enabled = True
    await db_session.commit()

    # Disable notifications
    response = await client.patch(
        f"/api/v1/cafes/{unlinked_cafe.id}/notifications",
        json={"enabled": False},
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notifications_enabled"] is False


async def test_update_notifications_cafe_not_linked(
    client, unlinked_cafe, manager_auth_headers
):
    """Test updating notifications for unlinked cafe returns 400."""
    response = await client.patch(
        f"/api/v1/cafes/{unlinked_cafe.id}/notifications",
        json={"enabled": False},
        headers=manager_auth_headers,
    )

    assert response.status_code == 400
    assert "not linked" in response.json()["detail"]


async def test_unlink_cafe_endpoint(
    client, db_session, unlinked_cafe, manager_auth_headers
):
    """Test DELETE /cafes/{cafe_id}/link endpoint."""
    # Link cafe first
    unlinked_cafe.tg_chat_id = 123456789
    unlinked_cafe.tg_username = "test_bot"
    await db_session.commit()

    # Unlink
    response = await client.delete(
        f"/api/v1/cafes/{unlinked_cafe.id}/link",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tg_chat_id"] is None
    assert data["tg_username"] is None


async def test_list_requests_filter_by_status(
    client, unlinked_cafe, manager_auth_headers, db_session
):
    """Test filtering requests by status."""
    # Create and approve some requests
    for i in range(2):
        create_response = await client.post(
            f"/api/v1/cafes/{unlinked_cafe.id}/link-request",
            json={
                "tg_chat_id": 123456789 + i,
                "tg_username": f"bot_{i}",
            },
        )
        request_id = create_response.json()["id"]

        if i == 0:
            # Approve first one
            await client.post(
                f"/api/v1/cafes/cafe-requests/{request_id}/approve",
                headers=manager_auth_headers,
            )
            # Unlink to allow next request
            unlinked_cafe.tg_chat_id = None
            await db_session.commit()

    # Filter by pending
    response = await client.get(
        "/api/v1/cafes/cafe-requests?status=pending",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert all(item["status"] == "pending" for item in data["items"])

    # Filter by approved
    response = await client.get(
        "/api/v1/cafes/cafe-requests?status=approved",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert all(item["status"] == "approved" for item in data["items"])
