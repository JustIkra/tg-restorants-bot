"""Unit tests for Cafe Link Service."""

import pytest
from fastapi import HTTPException

from src.models.cafe import Cafe, CafeLinkRequest, LinkRequestStatus
from src.schemas.cafe_link import CreateLinkRequestSchema
from src.services.cafe_link import CafeLinkService


@pytest.fixture
async def cafe_link_service(db_session):
    """Create CafeLinkService instance."""
    return CafeLinkService(db_session)


@pytest.fixture
async def test_cafe_for_linking(db_session):
    """Create a test cafe for linking tests."""
    cafe = Cafe(
        name="Linkable Cafe",
        description="A cafe for linking tests",
        is_active=True,
        tg_chat_id=None,  # Not linked yet
        tg_username=None,
        notifications_enabled=True,
        linked_at=None,
    )
    db_session.add(cafe)
    await db_session.commit()
    await db_session.refresh(cafe)
    return cafe


async def test_create_link_request_success(
    cafe_link_service, test_cafe_for_linking
):
    """Test successful creation of a link request."""
    data = CreateLinkRequestSchema(
        tg_chat_id=123456789,
        tg_username="test_cafe_bot",
    )

    request = await cafe_link_service.create_link_request(
        test_cafe_for_linking.id, data
    )

    assert request.cafe_id == test_cafe_for_linking.id
    assert request.tg_chat_id == 123456789
    assert request.tg_username == "test_cafe_bot"
    assert request.status == LinkRequestStatus.PENDING


async def test_create_link_request_cafe_not_found(cafe_link_service):
    """Test that creating link request for non-existent cafe raises 404."""
    data = CreateLinkRequestSchema(
        tg_chat_id=123456789,
        tg_username="test_cafe_bot",
    )

    with pytest.raises(HTTPException) as exc_info:
        await cafe_link_service.create_link_request(99999, data)

    assert exc_info.value.status_code == 404
    assert "Cafe not found" in exc_info.value.detail


async def test_create_link_request_cafe_already_linked(
    db_session, cafe_link_service, test_cafe_for_linking
):
    """Test that creating link request for already linked cafe raises 400."""
    # Link the cafe first
    test_cafe_for_linking.tg_chat_id = 987654321
    await db_session.commit()

    data = CreateLinkRequestSchema(
        tg_chat_id=123456789,
        tg_username="test_cafe_bot",
    )

    with pytest.raises(HTTPException) as exc_info:
        await cafe_link_service.create_link_request(
            test_cafe_for_linking.id, data
        )

    assert exc_info.value.status_code == 400
    assert "already linked" in exc_info.value.detail


async def test_create_link_request_pending_exists(
    db_session, cafe_link_service, test_cafe_for_linking
):
    """Test that creating duplicate pending request raises 400."""
    # Create first request
    data = CreateLinkRequestSchema(
        tg_chat_id=123456789,
        tg_username="test_cafe_bot",
    )
    await cafe_link_service.create_link_request(test_cafe_for_linking.id, data)

    # Try to create another pending request
    data2 = CreateLinkRequestSchema(
        tg_chat_id=111111111,
        tg_username="another_bot",
    )

    with pytest.raises(HTTPException) as exc_info:
        await cafe_link_service.create_link_request(
            test_cafe_for_linking.id, data2
        )

    assert exc_info.value.status_code == 400
    assert "already a pending request" in exc_info.value.detail


async def test_approve_request_updates_cafe(
    db_session, cafe_link_service, test_cafe_for_linking
):
    """Test that approving request updates cafe with Telegram data."""
    # Create request
    data = CreateLinkRequestSchema(
        tg_chat_id=123456789,
        tg_username="test_cafe_bot",
    )
    request = await cafe_link_service.create_link_request(
        test_cafe_for_linking.id, data
    )

    # Approve request
    approved = await cafe_link_service.approve_request(request.id)

    assert approved.status == LinkRequestStatus.APPROVED
    assert approved.processed_at is not None

    # Check cafe was updated
    await db_session.refresh(test_cafe_for_linking)
    assert test_cafe_for_linking.tg_chat_id == 123456789
    assert test_cafe_for_linking.tg_username == "test_cafe_bot"
    assert test_cafe_for_linking.notifications_enabled is True
    assert test_cafe_for_linking.linked_at is not None


async def test_approve_request_non_pending_fails(
    db_session, cafe_link_service, test_cafe_for_linking
):
    """Test that approving non-pending request raises 400."""
    # Create and approve request
    data = CreateLinkRequestSchema(
        tg_chat_id=123456789,
        tg_username="test_cafe_bot",
    )
    request = await cafe_link_service.create_link_request(
        test_cafe_for_linking.id, data
    )
    await cafe_link_service.approve_request(request.id)

    # Try to approve again
    with pytest.raises(HTTPException) as exc_info:
        await cafe_link_service.approve_request(request.id)

    assert exc_info.value.status_code == 400
    assert "already" in exc_info.value.detail


async def test_reject_request_changes_status(
    cafe_link_service, test_cafe_for_linking
):
    """Test that rejecting request changes status without updating cafe."""
    # Create request
    data = CreateLinkRequestSchema(
        tg_chat_id=123456789,
        tg_username="test_cafe_bot",
    )
    request = await cafe_link_service.create_link_request(
        test_cafe_for_linking.id, data
    )

    # Reject request
    rejected = await cafe_link_service.reject_request(request.id)

    assert rejected.status == LinkRequestStatus.REJECTED
    assert rejected.processed_at is not None

    # Check cafe was NOT updated
    assert test_cafe_for_linking.tg_chat_id is None
    assert test_cafe_for_linking.tg_username is None


async def test_update_notifications_enabled(
    db_session, cafe_link_service, test_cafe_for_linking
):
    """Test updating notification settings."""
    # Link cafe first
    test_cafe_for_linking.tg_chat_id = 123456789
    test_cafe_for_linking.notifications_enabled = True
    await db_session.commit()

    # Disable notifications
    cafe = await cafe_link_service.update_notifications(
        test_cafe_for_linking.id, False
    )

    assert cafe.notifications_enabled is False


async def test_update_notifications_cafe_not_linked_fails(
    cafe_link_service, test_cafe_for_linking
):
    """Test that updating notifications for unlinked cafe raises 400."""
    with pytest.raises(HTTPException) as exc_info:
        await cafe_link_service.update_notifications(
            test_cafe_for_linking.id, False
        )

    assert exc_info.value.status_code == 400
    assert "not linked" in exc_info.value.detail


async def test_unlink_cafe_clears_telegram_data(
    db_session, cafe_link_service, test_cafe_for_linking
):
    """Test that unlink_cafe clears Telegram data."""
    # Link cafe first
    test_cafe_for_linking.tg_chat_id = 123456789
    test_cafe_for_linking.tg_username = "test_bot"
    test_cafe_for_linking.notifications_enabled = True
    await db_session.commit()

    # Unlink
    cafe = await cafe_link_service.unlink_cafe(test_cafe_for_linking.id)

    assert cafe.tg_chat_id is None
    assert cafe.tg_username is None
    assert cafe.notifications_enabled is True  # Should keep this setting
    assert cafe.linked_at is None


async def test_list_requests_pagination(
    cafe_link_service, test_cafe_for_linking, db_session
):
    """Test list_requests with pagination."""
    # Create multiple cafes and requests (can't create multiple pending requests for same cafe)
    from src.models.cafe import Cafe

    cafes = []
    for i in range(5):
        cafe = Cafe(
            name=f"Test Cafe {i}",
            description="Test cafe",
            is_active=True,
        )
        db_session.add(cafe)
        cafes.append(cafe)

    await db_session.commit()

    # Create requests for different cafes
    for i, cafe in enumerate(cafes):
        await db_session.refresh(cafe)
        data = CreateLinkRequestSchema(
            tg_chat_id=123456789 + i,
            tg_username=f"bot_{i}",
        )
        await cafe_link_service.create_link_request(cafe.id, data)

    # List with pagination
    result = await cafe_link_service.list_requests(skip=0, limit=3)

    assert result["total"] == 5
    assert len(result["items"]) == 3
    assert result["skip"] == 0
    assert result["limit"] == 3


async def test_list_requests_filter_by_status(
    db_session, cafe_link_service, test_cafe_for_linking
):
    """Test list_requests filtering by status."""
    # Create and approve some requests
    for i in range(3):
        data = CreateLinkRequestSchema(
            tg_chat_id=123456789 + i,
            tg_username=f"bot_{i}",
        )
        request = await cafe_link_service.create_link_request(
            test_cafe_for_linking.id, data
        )

        if i < 2:
            # Approve first 2, leave last one pending
            await cafe_link_service.approve_request(request.id)
            # Unlink cafe to allow next request
            test_cafe_for_linking.tg_chat_id = None
            await db_session.commit()

    # Filter by pending
    result = await cafe_link_service.list_requests(
        status=LinkRequestStatus.PENDING
    )
    assert len(result["items"]) == 1

    # Filter by approved
    result = await cafe_link_service.list_requests(
        status=LinkRequestStatus.APPROVED
    )
    assert len(result["items"]) == 2
