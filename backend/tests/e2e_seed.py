#!/usr/bin/env python3
"""
E2E Test Seed Script for Backend

This script prepares the test database with realistic data for end-to-end testing.
It creates a test user, cafe, combos, menu items, and deadlines.

Usage:
    python tests/e2e_seed.py

Test User:
    - TGID: 968116200
    - Name: E2E Test User
    - Office: Test Office
    - Role: manager

The script is idempotent - it can be run multiple times without creating duplicates.
"""

import asyncio
import os
import sys
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models.base import Base
from src.models.cafe import Cafe, Combo, MenuItem
from src.models.deadline import Deadline
from src.models.user import User

# Test user TGIDs
TEST_USER_TGID = 968116200
TEST_USER_TGID_2 = 6055257779

# Database URL - use from environment or default to test database
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/lunch_bot_test"
)


async def seed_database():
    """Seed the test database with realistic data for e2e tests."""
    print(f"[E2E Seed] Connecting to database: {DATABASE_URL}")

    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Create tables if they don't exist
    print("[E2E Seed] Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        try:
            # 1. Create or update test user
            print(f"[E2E Seed] Creating test user (tgid={TEST_USER_TGID})...")
            result = await session.execute(select(User).where(User.tgid == TEST_USER_TGID))
            user = result.scalar_one_or_none()

            if user is None:
                user = User(
                    tgid=TEST_USER_TGID,
                    name="E2E Test User",
                    office="Test Office",
                    role="manager",
                    is_active=True,
                    weekly_limit=Decimal("500.00"),
                )
                session.add(user)
                print(f"  ✓ Created user: {user.name} (tgid={user.tgid})")
            else:
                user.name = "E2E Test User"
                user.office = "Test Office"
                user.is_active = True
                user.weekly_limit = Decimal("500.00")
                print(f"  ✓ Updated user: {user.name} (tgid={user.tgid})")

            await session.flush()

            # 1.5 Create or update second test user
            print(f"[E2E Seed] Creating second test user (tgid={TEST_USER_TGID_2})...")
            result = await session.execute(select(User).where(User.tgid == TEST_USER_TGID_2))
            user2 = result.scalar_one_or_none()

            if user2 is None:
                user2 = User(
                    tgid=TEST_USER_TGID_2,
                    name="Test User 2",
                    office="Test Office",
                    role="user",
                    is_active=True,
                    weekly_limit=Decimal("500.00"),
                )
                session.add(user2)
                print(f"  ✓ Created user: {user2.name} (tgid={user2.tgid})")
            else:
                user2.name = "Test User 2"
                user2.office = "Test Office"
                user2.is_active = True
                user2.weekly_limit = Decimal("500.00")
                print(f"  ✓ Updated user: {user2.name} (tgid={user2.tgid})")

            await session.flush()

            # 2. Create or update test cafe
            print("[E2E Seed] Creating test cafe...")
            result = await session.execute(select(Cafe).where(Cafe.name == "E2E Test Cafe"))
            cafe = result.scalar_one_or_none()

            if cafe is None:
                cafe = Cafe(
                    name="E2E Test Cafe",
                    description="Test cafe for end-to-end testing",
                    is_active=True,
                )
                session.add(cafe)
                print(f"  ✓ Created cafe: {cafe.name}")
            else:
                cafe.is_active = True
                cafe.description = "Test cafe for end-to-end testing"
                print(f"  ✓ Updated cafe: {cafe.name}")

            await session.flush()
            cafe_id = cafe.id

            # 3. Create combos
            print("[E2E Seed] Creating combos...")

            # Combo 1: Basic Lunch (soup + main + salad)
            result = await session.execute(
                select(Combo).where(
                    Combo.cafe_id == cafe_id,
                    Combo.name == "Basic Lunch"
                )
            )
            combo1 = result.scalar_one_or_none()

            if combo1 is None:
                combo1 = Combo(
                    cafe_id=cafe_id,
                    name="Basic Lunch",
                    categories=["soup", "main", "salad"],
                    price=Decimal("15.00"),
                    is_available=True,
                )
                session.add(combo1)
                print(f"  ✓ Created combo: {combo1.name} - ${combo1.price}")
            else:
                combo1.is_available = True
                combo1.price = Decimal("15.00")
                print(f"  ✓ Updated combo: {combo1.name} - ${combo1.price}")

            # Combo 2: Light Lunch (salad + main)
            result = await session.execute(
                select(Combo).where(
                    Combo.cafe_id == cafe_id,
                    Combo.name == "Light Lunch"
                )
            )
            combo2 = result.scalar_one_or_none()

            if combo2 is None:
                combo2 = Combo(
                    cafe_id=cafe_id,
                    name="Light Lunch",
                    categories=["salad", "main"],
                    price=Decimal("12.00"),
                    is_available=True,
                )
                session.add(combo2)
                print(f"  ✓ Created combo: {combo2.name} - ${combo2.price}")
            else:
                combo2.is_available = True
                combo2.price = Decimal("12.00")
                print(f"  ✓ Updated combo: {combo2.name} - ${combo2.price}")

            await session.flush()

            # 4. Create menu items
            print("[E2E Seed] Creating menu items...")

            menu_items_data = [
                # Soups
                {
                    "name": "Tomato Soup",
                    "description": "Classic tomato soup with basil",
                    "category": "soup",
                    "price": None,
                },
                {
                    "name": "Chicken Noodle Soup",
                    "description": "Homemade chicken soup with noodles",
                    "category": "soup",
                    "price": None,
                },
                {
                    "name": "Mushroom Cream Soup",
                    "description": "Creamy mushroom soup",
                    "category": "soup",
                    "price": None,
                },
                # Main courses
                {
                    "name": "Grilled Chicken",
                    "description": "Grilled chicken breast with vegetables",
                    "category": "main",
                    "price": None,
                },
                {
                    "name": "Beef Steak",
                    "description": "Grilled beef steak with potatoes",
                    "category": "main",
                    "price": None,
                },
                {
                    "name": "Fish & Chips",
                    "description": "Crispy fish with french fries",
                    "category": "main",
                    "price": None,
                },
                {
                    "name": "Vegetarian Pasta",
                    "description": "Pasta with seasonal vegetables",
                    "category": "main",
                    "price": None,
                },
                # Salads
                {
                    "name": "Caesar Salad",
                    "description": "Classic Caesar salad with parmesan",
                    "category": "salad",
                    "price": None,
                },
                {
                    "name": "Greek Salad",
                    "description": "Fresh Greek salad with feta cheese",
                    "category": "salad",
                    "price": None,
                },
                {
                    "name": "Garden Salad",
                    "description": "Mixed greens with seasonal vegetables",
                    "category": "salad",
                    "price": None,
                },
                # Extras (with prices)
                {
                    "name": "Coffee",
                    "description": "Freshly brewed coffee",
                    "category": "extra",
                    "price": Decimal("2.50"),
                },
                {
                    "name": "Tea",
                    "description": "Selection of teas",
                    "category": "extra",
                    "price": Decimal("2.00"),
                },
                {
                    "name": "Orange Juice",
                    "description": "Freshly squeezed orange juice",
                    "category": "extra",
                    "price": Decimal("3.50"),
                },
                {
                    "name": "Chocolate Cake",
                    "description": "Homemade chocolate cake",
                    "category": "extra",
                    "price": Decimal("4.50"),
                },
                {
                    "name": "Ice Cream",
                    "description": "Vanilla ice cream",
                    "category": "extra",
                    "price": Decimal("3.00"),
                },
            ]

            for item_data in menu_items_data:
                result = await session.execute(
                    select(MenuItem).where(
                        MenuItem.cafe_id == cafe_id,
                        MenuItem.name == item_data["name"]
                    )
                )
                item = result.scalar_one_or_none()

                if item is None:
                    item = MenuItem(
                        cafe_id=cafe_id,
                        name=item_data["name"],
                        description=item_data["description"],
                        category=item_data["category"],
                        price=item_data["price"],
                        is_available=True,
                    )
                    session.add(item)
                    price_str = f"${item.price}" if item.price else "included"
                    print(f"  ✓ Created menu item: {item.name} ({item.category}) - {price_str}")
                else:
                    item.description = item_data["description"]
                    item.price = item_data["price"]
                    item.is_available = True
                    price_str = f"${item.price}" if item.price else "included"
                    print(f"  ✓ Updated menu item: {item.name} ({item.category}) - {price_str}")

            await session.flush()

            # 5. Create deadlines for all weekdays
            print("[E2E Seed] Creating deadlines...")

            weekdays = [
                (0, "Monday"),
                (1, "Tuesday"),
                (2, "Wednesday"),
                (3, "Thursday"),
                (4, "Friday"),
            ]

            for weekday, day_name in weekdays:
                result = await session.execute(
                    select(Deadline).where(
                        Deadline.cafe_id == cafe_id,
                        Deadline.weekday == weekday
                    )
                )
                deadline = result.scalar_one_or_none()

                if deadline is None:
                    deadline = Deadline(
                        cafe_id=cafe_id,
                        weekday=weekday,
                        deadline_time="10:00",
                        is_enabled=True,
                        advance_days=1,  # Order 1 day in advance
                    )
                    session.add(deadline)
                    print(f"  ✓ Created deadline: {day_name} - 10:00 (1 day advance)")
                else:
                    deadline.deadline_time = "10:00"
                    deadline.is_enabled = True
                    deadline.advance_days = 1
                    print(f"  ✓ Updated deadline: {day_name} - 10:00 (1 day advance)")

            # Commit all changes
            await session.commit()
            print("\n[E2E Seed] ✓ Database seeding completed successfully!")
            print(f"\nTest user TGIDs: {TEST_USER_TGID}, {TEST_USER_TGID_2}")
            print(f"Test cafe ID: {cafe_id}")
            print(f"Combos created: 2")
            print(f"Menu items created: {len(menu_items_data)}")
            print(f"Deadlines created: {len(weekdays)}")

        except Exception as e:
            await session.rollback()
            print(f"\n[E2E Seed] ✗ Error seeding database: {e}")
            raise
        finally:
            await session.close()

    await engine.dispose()


async def clear_test_data():
    """Clear only test-related data (orders for test user)."""
    print(f"[E2E Seed] Clearing test data...")

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        try:
            from src.models.order import Order

            # Delete orders for test user
            result = await session.execute(
                select(Order).where(Order.user_tgid == TEST_USER_TGID)
            )
            orders = result.scalars().all()

            for order in orders:
                await session.delete(order)

            await session.commit()
            print(f"[E2E Seed] ✓ Cleared {len(orders)} test orders")

        except Exception as e:
            await session.rollback()
            print(f"[E2E Seed] ✗ Error clearing test data: {e}")
            raise
        finally:
            await session.close()

    await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="E2E Test Database Seeder")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear test data (orders) instead of seeding"
    )
    args = parser.parse_args()

    if args.clear:
        asyncio.run(clear_test_data())
    else:
        asyncio.run(seed_database())
