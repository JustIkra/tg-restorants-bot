from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_tgid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tgid"), nullable=False)
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafes.id"), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    combo_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("combos.id"), nullable=True)
    items: Mapped[list] = mapped_column("combo_items", JSON, nullable=False)  # Renamed from combo_items, supports combo and standalone
    extras: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # [{ menu_item_id, quantity }]
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    cafe: Mapped["Cafe"] = relationship("Cafe", back_populates="orders")
    combo: Mapped["Combo | None"] = relationship("Combo", back_populates="orders")

    @property
    def combo_items(self):
        """Deprecated (read-only). Use 'items' instead. Kept for backward compatibility."""
        return self.items
