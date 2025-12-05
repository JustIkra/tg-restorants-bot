from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.summary import SummaryRepository
from ..schemas.summary import SummaryCreate


class SummaryService:
    def __init__(self, session: AsyncSession):
        self.repo = SummaryRepository(session)

    async def list_summaries(
        self,
        cafe_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ):
        return await self.repo.list(cafe_id=cafe_id, skip=skip, limit=limit)

    async def get_summary(self, summary_id: int):
        summary = await self.repo.get(summary_id)
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found",
            )
        return summary

    async def create_summary(self, data: SummaryCreate):
        """
        Generate a summary report for a specific cafe and date.
        Aggregates all orders and creates breakdown by combos and extras.
        """
        orders = await self.repo.get_orders_for_date(data.cafe_id, data.date)

        if not orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No orders found for this date",
            )

        # Aggregate data
        total_orders = len(orders)
        total_amount = sum(order.total_price for order in orders)

        # Build breakdown
        combo_counts: dict[int, dict] = {}
        extra_counts: dict[int, dict] = {}

        for order in orders:
            # Count combos
            combo_id = order.combo_id
            if combo_id not in combo_counts:
                combo = await self.repo.get_combo(combo_id)
                combo_counts[combo_id] = {
                    "name": combo.name if combo else f"Combo {combo_id}",
                    "quantity": 0,
                    "amount": Decimal("0"),
                }
            combo_counts[combo_id]["quantity"] += 1
            if combo:
                combo_counts[combo_id]["amount"] += combo.price

            # Count extras
            for extra in order.extras:
                item_id = extra["menu_item_id"]
                quantity = extra.get("quantity", 1)

                if item_id not in extra_counts:
                    item = await self.repo.get_menu_item(item_id)
                    extra_counts[item_id] = {
                        "name": item.name if item else f"Item {item_id}",
                        "quantity": 0,
                        "amount": Decimal("0"),
                    }
                extra_counts[item_id]["quantity"] += quantity
                if item and item.price:
                    extra_counts[item_id]["amount"] += item.price * quantity

        breakdown = {
            "combos": [
                {"id": k, **v} for k, v in combo_counts.items()
            ],
            "extras": [
                {"id": k, **v} for k, v in extra_counts.items()
            ],
        }

        # Create summary
        return await self.repo.create(
            cafe_id=data.cafe_id,
            date=data.date,
            total_orders=total_orders,
            total_amount=total_amount,
            breakdown=breakdown,
        )

    async def delete_summary(self, summary_id: int):
        summary = await self.get_summary(summary_id)
        await self.repo.delete(summary)

    def format_summary_csv(self, summary) -> str:
        """Format summary as CSV string."""
        lines = [
            f"Summary Report: {summary.date}",
            f"Cafe ID: {summary.cafe_id}",
            f"Total Orders: {summary.total_orders}",
            f"Total Amount: {summary.total_amount}",
            "",
            "Combos:",
            "Name,Quantity,Amount",
        ]

        for combo in summary.breakdown.get("combos", []):
            lines.append(f"{combo['name']},{combo['quantity']},{combo['amount']}")

        lines.extend([
            "",
            "Extras:",
            "Name,Quantity,Amount",
        ])

        for extra in summary.breakdown.get("extras", []):
            lines.append(f"{extra['name']},{extra['quantity']},{extra['amount']}")

        return "\n".join(lines)
