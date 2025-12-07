"""Integration tests for Deadlines API."""

import pytest


@pytest.mark.asyncio
async def test_get_deadlines_empty_schedule(client, test_cafe, manager_auth_headers):
    """Test getting empty deadline schedule for a cafe."""
    response = await client.get(
        f"/api/v1/cafes/{test_cafe.id}/deadlines",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cafe_id"] == test_cafe.id
    assert isinstance(data["schedule"], list)
    # Empty schedule initially
    assert len(data["schedule"]) == 0


@pytest.mark.asyncio
async def test_get_deadlines_with_schedule(client, test_cafe, test_deadline, manager_auth_headers):
    """Test getting deadline schedule with existing deadlines."""
    response = await client.get(
        f"/api/v1/cafes/{test_cafe.id}/deadlines",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cafe_id"] == test_cafe.id
    assert len(data["schedule"]) == 1

    schedule_item = data["schedule"][0]
    assert schedule_item["weekday"] == 0  # Monday
    assert schedule_item["deadline_time"] == "10:00"
    assert schedule_item["is_enabled"] is True
    assert schedule_item["advance_days"] == 1


@pytest.mark.asyncio
async def test_get_deadlines_user_forbidden(client, test_cafe, auth_headers):
    """Test regular user cannot access deadlines (manager only)."""
    response = await client.get(
        f"/api/v1/cafes/{test_cafe.id}/deadlines",
        headers=auth_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_deadlines_manager(client, test_cafe, manager_auth_headers):
    """Test manager can update deadline schedule."""
    schedule_data = {
        "schedule": [
            {
                "weekday": 0,  # Monday
                "deadline_time": "09:00",
                "is_enabled": True,
                "advance_days": 0,
            },
            {
                "weekday": 1,  # Tuesday
                "deadline_time": "10:30",
                "is_enabled": True,
                "advance_days": 1,
            },
            {
                "weekday": 2,  # Wednesday
                "deadline_time": "11:00",
                "is_enabled": False,
                "advance_days": 0,
            },
        ]
    }

    response = await client.put(
        f"/api/v1/cafes/{test_cafe.id}/deadlines",
        headers=manager_auth_headers,
        json=schedule_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cafe_id"] == test_cafe.id
    assert len(data["schedule"]) == 3

    # Verify first item
    assert data["schedule"][0]["weekday"] == 0
    assert data["schedule"][0]["deadline_time"] == "09:00"
    assert data["schedule"][0]["is_enabled"] is True
    assert data["schedule"][0]["advance_days"] == 0

    # Verify second item
    assert data["schedule"][1]["weekday"] == 1
    assert data["schedule"][1]["deadline_time"] == "10:30"
    assert data["schedule"][1]["is_enabled"] is True
    assert data["schedule"][1]["advance_days"] == 1

    # Verify third item (disabled)
    assert data["schedule"][2]["weekday"] == 2
    assert data["schedule"][2]["is_enabled"] is False


@pytest.mark.asyncio
async def test_update_deadlines_replaces_existing(client, test_cafe, test_deadline, manager_auth_headers):
    """Test updating deadlines replaces existing schedule."""
    # test_deadline creates Monday with 10:00, advance_days=1
    new_schedule_data = {
        "schedule": [
            {
                "weekday": 0,  # Monday
                "deadline_time": "12:00",  # Changed time
                "is_enabled": True,
                "advance_days": 2,  # Changed advance_days
            },
        ]
    }

    response = await client.put(
        f"/api/v1/cafes/{test_cafe.id}/deadlines",
        headers=manager_auth_headers,
        json=new_schedule_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["schedule"]) == 1
    assert data["schedule"][0]["deadline_time"] == "12:00"
    assert data["schedule"][0]["advance_days"] == 2


@pytest.mark.asyncio
async def test_update_deadlines_user_forbidden(client, test_cafe, auth_headers):
    """Test regular user cannot update deadlines."""
    schedule_data = {
        "schedule": [
            {
                "weekday": 0,
                "deadline_time": "10:00",
                "is_enabled": True,
                "advance_days": 1,
            },
        ]
    }

    response = await client.put(
        f"/api/v1/cafes/{test_cafe.id}/deadlines",
        headers=auth_headers,
        json=schedule_data,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_deadlines_full_week_schedule(client, test_cafe, manager_auth_headers):
    """Test creating full week schedule (Monday-Sunday)."""
    schedule_data = {
        "schedule": [
            {"weekday": i, "deadline_time": "10:00", "is_enabled": True, "advance_days": 1}
            for i in range(7)
        ]
    }

    response = await client.put(
        f"/api/v1/cafes/{test_cafe.id}/deadlines",
        headers=manager_auth_headers,
        json=schedule_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["schedule"]) == 7

    # Verify all weekdays present
    weekdays = [item["weekday"] for item in data["schedule"]]
    assert sorted(weekdays) == list(range(7))


@pytest.mark.asyncio
async def test_update_deadlines_clear_schedule(client, test_cafe, test_deadline, manager_auth_headers):
    """Test clearing schedule by sending empty array."""
    schedule_data = {
        "schedule": []
    }

    response = await client.put(
        f"/api/v1/cafes/{test_cafe.id}/deadlines",
        headers=manager_auth_headers,
        json=schedule_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["schedule"]) == 0
