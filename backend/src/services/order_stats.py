from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import MenuItem, Order


class OrderStatsService:
    """
    Сбор и анализ статистики заказов для рекомендаций Gemini.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_stats(self, user_tgid: int, days: int = 30) -> dict[str, Any]:
        """
        Собирает статистику заказов пользователя за последние N дней.

        Args:
            user_tgid: Telegram ID пользователя
            days: Количество дней для анализа (по умолчанию 30)

        Returns:
            {
                "orders_count": int,
                "categories": {
                    "Горячее": {"count": 10, "percent": 40.0},
                    "Салаты": {"count": 5, "percent": 20.0},
                    ...
                },
                "unique_dishes": int,
                "total_dishes_available": int,
                "favorite_dishes": [
                    {"name": "Борщ", "count": 5},
                    {"name": "Цезарь", "count": 3},
                    ...
                ],
                "last_order_date": datetime | None
            }
        """
        since = datetime.now() - timedelta(days=days)

        orders_count = await self._count_orders(user_tgid, since)
        categories = await self._get_categories_distribution(user_tgid, since)
        unique_dishes = await self._count_unique_dishes(user_tgid, since)
        total_dishes = await self._get_total_dishes_count()
        favorite_dishes = await self._get_favorite_dishes(user_tgid, since)
        last_order_date = await self._get_last_order_date(user_tgid)

        return {
            "orders_count": orders_count,
            "categories": categories,
            "unique_dishes": unique_dishes,
            "total_dishes_available": total_dishes,
            "favorite_dishes": favorite_dishes,
            "last_order_date": last_order_date,
        }

    async def get_active_users(self, min_orders: int = 5, days: int = 30) -> list[int]:
        """
        Получает список tgid пользователей с >= min_orders заказов за days дней.
        Используется для batch генерации рекомендаций.

        Args:
            min_orders: Минимальное количество заказов
            days: Период в днях

        Returns:
            Список Telegram ID активных пользователей
        """
        since = datetime.now() - timedelta(days=days)

        result = await self.session.execute(
            select(Order.user_tgid, func.count(Order.id).label("order_count"))
            .where(Order.created_at >= since)
            .group_by(Order.user_tgid)
            .having(func.count(Order.id) >= min_orders)
        )

        return [row.user_tgid for row in result.all()]

    async def _count_orders(self, user_tgid: int, since: datetime) -> int:
        """
        Подсчет заказов пользователя с указанной даты.
        """
        result = await self.session.execute(
            select(func.count(Order.id)).where(
                Order.user_tgid == user_tgid, Order.created_at >= since
            )
        )
        return result.scalar() or 0

    async def _get_categories_distribution(
        self, user_tgid: int, since: datetime
    ) -> dict[str, dict[str, Any]]:
        """
        Распределение заказов по категориям блюд.

        Анализирует combo_items каждого заказа для подсчета категорий.

        Returns:
            {
                "soup": {"count": 10, "percent": 33.3},
                "salad": {"count": 8, "percent": 26.7},
                "main": {"count": 12, "percent": 40.0},
            }
        """
        # Получаем все заказы пользователя за период
        result = await self.session.execute(
            select(Order.combo_items).where(Order.user_tgid == user_tgid, Order.created_at >= since)
        )

        # Подсчитываем категории из combo_items
        category_counts: dict[str, int] = {}
        total_items = 0

        for (combo_items,) in result.all():
            for item in combo_items:
                category = item.get("category")
                if category:
                    category_counts[category] = category_counts.get(category, 0) + 1
                    total_items += 1

        # Вычисляем проценты
        categories_distribution: dict[str, dict[str, Any]] = {}
        for category, count in category_counts.items():
            percent = (count / total_items * 100) if total_items > 0 else 0
            categories_distribution[category] = {"count": count, "percent": round(percent, 1)}

        return categories_distribution

    async def _count_unique_dishes(self, user_tgid: int, since: datetime) -> int:
        """
        Количество уникальных блюд, которые пользователь заказывал.
        """
        # Получаем все заказы с combo_items и extras
        result = await self.session.execute(
            select(Order.combo_items, Order.extras).where(
                Order.user_tgid == user_tgid, Order.created_at >= since
            )
        )

        unique_dish_ids: set[int] = set()

        for combo_items, extras in result.all():
            # Собираем ID из combo_items
            for item in combo_items:
                menu_item_id = item.get("menu_item_id")
                if menu_item_id:
                    unique_dish_ids.add(menu_item_id)

            # Собираем ID из extras
            for extra in extras:
                menu_item_id = extra.get("menu_item_id")
                if menu_item_id:
                    unique_dish_ids.add(menu_item_id)

        return len(unique_dish_ids)

    async def _get_total_dishes_count(self) -> int:
        """
        Общее количество блюд в меню (всех кафе).
        """
        result = await self.session.execute(
            select(func.count(MenuItem.id)).where(MenuItem.is_available == True)  # noqa: E712
        )
        return result.scalar() or 0

    async def _get_favorite_dishes(
        self, user_tgid: int, since: datetime, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Топ N любимых блюд пользователя.

        Returns:
            [
                {"name": "Борщ", "count": 5},
                {"name": "Цезарь", "count": 3},
                ...
            ]
        """
        # Получаем все заказы
        result = await self.session.execute(
            select(Order.combo_items, Order.extras).where(
                Order.user_tgid == user_tgid, Order.created_at >= since
            )
        )

        # Подсчитываем частоту блюд
        dish_counts: dict[int, int] = {}

        for combo_items, extras in result.all():
            # Считаем из combo_items
            for item in combo_items:
                menu_item_id = item.get("menu_item_id")
                if menu_item_id:
                    dish_counts[menu_item_id] = dish_counts.get(menu_item_id, 0) + 1

            # Считаем из extras (с учетом quantity)
            for extra in extras:
                menu_item_id = extra.get("menu_item_id")
                quantity = extra.get("quantity", 1)
                if menu_item_id:
                    dish_counts[menu_item_id] = dish_counts.get(menu_item_id, 0) + quantity

        # Сортируем по убыванию частоты
        top_dish_ids = sorted(dish_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        if not top_dish_ids:
            return []

        # Получаем названия блюд
        dish_ids = [dish_id for dish_id, _ in top_dish_ids]
        result = await self.session.execute(
            select(MenuItem.id, MenuItem.name).where(MenuItem.id.in_(dish_ids))
        )

        dish_names = {row.id: row.name for row in result.all()}

        # Формируем результат
        favorite_dishes = []
        for dish_id, count in top_dish_ids:
            name = dish_names.get(dish_id)
            if name:
                favorite_dishes.append({"name": name, "count": count})

        return favorite_dishes

    async def _get_last_order_date(self, user_tgid: int) -> datetime | None:
        """
        Получить дату последнего заказа пользователя.
        """
        result = await self.session.execute(
            select(Order.created_at)
            .where(Order.user_tgid == user_tgid)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row
