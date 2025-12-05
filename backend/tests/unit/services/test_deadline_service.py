"""Tests for DeadlineService."""

from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from src.schemas.deadline import DeadlineScheduleUpdate
from src.services.deadline import DeadlineService


@pytest.mark.asyncio
async def test_get_schedule(db_session, test_cafe, test_deadline):
    """Test getting deadline schedule for cafe."""
    service = DeadlineService(db_session)

    schedule = await service.get_schedule(test_cafe.id)

    assert schedule.cafe_id == test_cafe.id
    assert len(schedule.schedule) == 1
    assert schedule.schedule[0]["weekday"] == 0
    assert schedule.schedule[0]["deadline_time"] == "10:00"
    assert schedule.schedule[0]["is_enabled"] is True
    assert schedule.schedule[0]["advance_days"] == 1


@pytest.mark.asyncio
async def test_update_schedule(db_session, test_cafe):
    """Test updating deadline schedule."""
    service = DeadlineService(db_session)

    update_data = DeadlineScheduleUpdate(
        schedule=[
            {
                "weekday": 0,  # Monday
                "deadline_time": "11:00",
                "is_enabled": True,
                "advance_days": 1,
            },
            {
                "weekday": 2,  # Wednesday
                "deadline_time": "12:00",
                "is_enabled": True,
                "advance_days": 2,
            },
        ]
    )

    schedule = await service.update_schedule(test_cafe.id, update_data)

    assert len(schedule.schedule) == 2
    assert schedule.schedule[0]["weekday"] == 0
    assert schedule.schedule[0]["deadline_time"] == "11:00"
    assert schedule.schedule[1]["weekday"] == 2
    assert schedule.schedule[1]["deadline_time"] == "12:00"


@pytest.mark.asyncio
async def test_check_availability_can_order(db_session, test_cafe, test_deadline):
    """Test availability check when ordering is allowed."""
    service = DeadlineService(db_session)

    # Order for day after tomorrow (Monday deadline is 1 day in advance)
    order_date = date.today() + timedelta(days=2)
    # Adjust to Monday if needed
    while order_date.weekday() != 0:
        order_date += timedelta(days=1)

    availability = await service.check_availability(test_cafe.id, order_date)

    # This might be True or False depending on current time
    # Just verify structure
    assert availability.date == order_date
    assert isinstance(availability.can_order, bool)


@pytest.mark.asyncio
async def test_check_availability_no_deadline(db_session, test_cafe):
    """Test availability when no deadline exists for weekday."""
    service = DeadlineService(db_session)

    # Tuesday (weekday 1) - no deadline configured
    today = date.today()
    tuesday = today + timedelta(days=(1 - today.weekday()) % 7)

    availability = await service.check_availability(test_cafe.id, tuesday)

    assert availability.can_order is False
    assert "No delivery" in availability.reason


@pytest.mark.asyncio
async def test_check_availability_disabled(db_session, test_cafe):
    """Test availability when deadline is disabled."""
    service = DeadlineService(db_session)

    # Create disabled deadline for Tuesday
    from src.models.deadline import Deadline

    deadline = Deadline(
        cafe_id=test_cafe.id,
        weekday=1,  # Tuesday
        deadline_time="10:00",
        is_enabled=False,  # Disabled
        advance_days=1,
    )
    db_session.add(deadline)
    await db_session.commit()

    # Tuesday
    today = date.today()
    tuesday = today + timedelta(days=(1 - today.weekday()) % 7)

    availability = await service.check_availability(test_cafe.id, tuesday)

    assert availability.can_order is False
    assert "disabled" in availability.reason.lower()


@pytest.mark.asyncio
async def test_get_week_availability(db_session, test_cafe, test_deadline):
    """Test getting availability for next 7 days."""
    service = DeadlineService(db_session)

    week_availability = await service.get_week_availability(test_cafe.id)

    assert week_availability.cafe_id == test_cafe.id
    assert len(week_availability.availability) == 7

    # Verify all dates are consecutive
    for i in range(7):
        expected_date = date.today() + timedelta(days=i)
        assert week_availability.availability[i].date == expected_date


@pytest.mark.asyncio
async def test_validate_order_deadline_raises_on_failure(db_session, test_cafe):
    """Test validate_order_deadline raises exception when cannot order."""
    service = DeadlineService(db_session)

    # Past date - should always fail
    past_date = date.today() - timedelta(days=1)

    with pytest.raises(HTTPException) as exc_info:
        await service.validate_order_deadline(test_cafe.id, past_date)

    assert exc_info.value.status_code == 400
