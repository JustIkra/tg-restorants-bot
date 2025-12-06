"""Pytest fixtures for testing."""

import os

# Set environment variables BEFORE importing anything from src
# Token format: <bot_id>:<token> (bot_id must be numeric)
os.environ["TELEGRAM_BOT_TOKEN"] = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_at_least_32_chars_long_for_security"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["KAFKA_BROKER_URL"] = "localhost:9092"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["GEMINI_API_KEYS"] = "test_key_1,test_key_2,test_key_3"
os.environ["GEMINI_MODEL"] = "gemini-2.0-flash-exp"
os.environ["GEMINI_MAX_REQUESTS_PER_KEY"] = "195"

from collections.abc import AsyncGenerator
from datetime import date, datetime, time
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.auth.jwt import create_access_token
from src.database import get_db
from src.main import app
from src.models.base import Base
from src.models.cafe import Cafe, CafeLinkRequest, Combo, MenuItem
from src.models.deadline import Deadline
from src.models.order import Order
from src.models.user import User

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    return engine


@pytest.fixture(scope="session")
async def setup_database(test_engine):
    """Create all tables in test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_engine, setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Clean up tables after each test
            await session.execute(Order.__table__.delete())
            await session.execute(CafeLinkRequest.__table__.delete())
            await session.execute(Deadline.__table__.delete())
            await session.execute(MenuItem.__table__.delete())
            await session.execute(Combo.__table__.delete())
            await session.execute(Cafe.__table__.delete())
            await session.execute(User.__table__.delete())
            await session.commit()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with database session override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Test data fixtures


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        tgid=123456789,
        name="Test User",
        office="Office A",
        role="user",
        is_active=True,
        weekly_limit=Decimal("1000.00"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_manager(db_session: AsyncSession) -> User:
    """Create a test manager."""
    manager = User(
        tgid=987654321,
        name="Test Manager",
        office="Office A",
        role="manager",
        is_active=True,
    )
    db_session.add(manager)
    await db_session.commit()
    await db_session.refresh(manager)
    return manager


@pytest.fixture
async def test_cafe(db_session: AsyncSession) -> Cafe:
    """Create a test cafe."""
    cafe = Cafe(
        name="Test Cafe",
        description="A test cafe",
        is_active=True,
    )
    db_session.add(cafe)
    await db_session.commit()
    await db_session.refresh(cafe)
    return cafe


@pytest.fixture
async def test_combo(db_session: AsyncSession, test_cafe: Cafe) -> Combo:
    """Create a test combo."""
    combo = Combo(
        cafe_id=test_cafe.id,
        name="Combo A",
        categories=["soup", "main", "salad"],
        price=Decimal("15.00"),
        is_available=True,
    )
    db_session.add(combo)
    await db_session.commit()
    await db_session.refresh(combo)
    return combo


@pytest.fixture
async def test_menu_items(db_session: AsyncSession, test_cafe: Cafe) -> list[MenuItem]:
    """Create test menu items."""
    items = [
        MenuItem(
            cafe_id=test_cafe.id,
            name="Tomato Soup",
            description="Delicious soup",
            category="soup",
            is_available=True,
        ),
        MenuItem(
            cafe_id=test_cafe.id,
            name="Grilled Chicken",
            description="Tasty chicken",
            category="main",
            is_available=True,
        ),
        MenuItem(
            cafe_id=test_cafe.id,
            name="Caesar Salad",
            description="Fresh salad",
            category="salad",
            is_available=True,
        ),
        MenuItem(
            cafe_id=test_cafe.id,
            name="Coffee",
            description="Hot coffee",
            category="extra",
            price=Decimal("2.50"),
            is_available=True,
        ),
    ]
    for item in items:
        db_session.add(item)
    await db_session.commit()
    for item in items:
        await db_session.refresh(item)
    return items


@pytest.fixture
async def test_deadline(db_session: AsyncSession, test_cafe: Cafe) -> Deadline:
    """Create a test deadline for Monday (weekday 0)."""
    deadline = Deadline(
        cafe_id=test_cafe.id,
        weekday=0,  # Monday
        deadline_time="10:00",
        is_enabled=True,
        advance_days=1,  # Order 1 day in advance
    )
    db_session.add(deadline)
    await db_session.commit()
    await db_session.refresh(deadline)
    return deadline


@pytest.fixture
async def test_order(
    db_session: AsyncSession,
    test_user: User,
    test_cafe: Cafe,
    test_combo: Combo,
    test_menu_items: list[MenuItem],
) -> Order:
    """Create a test order."""
    # Order for next Monday (weekday 0) to match test_deadline
    from datetime import timedelta
    today = date.today()
    days_until_monday = (0 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # If today is Monday, order for next Monday
    order_date = today + timedelta(days=days_until_monday)

    order = Order(
        user_tgid=test_user.tgid,
        cafe_id=test_cafe.id,
        order_date=order_date,
        status="pending",
        combo_id=test_combo.id,
        combo_items=[
            {"category": "soup", "menu_item_id": test_menu_items[0].id},
            {"category": "main", "menu_item_id": test_menu_items[1].id},
            {"category": "salad", "menu_item_id": test_menu_items[2].id},
        ],
        extras=[{"menu_item_id": test_menu_items[3].id, "quantity": 1}],
        notes="No onions",
        total_price=Decimal("17.50"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


# Auth fixtures


@pytest.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Generate JWT auth headers for test user."""
    token = create_access_token({"tgid": test_user.tgid, "role": test_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def manager_auth_headers(test_manager: User) -> dict[str, str]:
    """Generate JWT auth headers for test manager."""
    token = create_access_token({"tgid": test_manager.tgid, "role": test_manager.role})
    return {"Authorization": f"Bearer {token}"}
