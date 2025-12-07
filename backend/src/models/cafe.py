from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class LinkRequestStatus(StrEnum):
    """Status of cafe link request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Cafe(Base, TimestampMixin):
    __tablename__ = "cafes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Telegram notification fields
    tg_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tg_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    combos: Mapped[list["Combo"]] = relationship("Combo", back_populates="cafe")
    menu_items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="cafe")
    deadlines: Mapped[list["Deadline"]] = relationship("Deadline", back_populates="cafe")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="cafe")
    summaries: Mapped[list["Summary"]] = relationship("Summary", back_populates="cafe")
    link_requests: Mapped[list["CafeLinkRequest"]] = relationship("CafeLinkRequest", back_populates="cafe")


class Combo(Base):
    __tablename__ = "combos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafes.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    categories: Mapped[list] = mapped_column(JSON, nullable=False)  # ["salad", "soup", "main"]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    cafe: Mapped["Cafe"] = relationship("Cafe", back_populates="combos")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="combo")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafes.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # soup, salad, main, extra
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # can be set for any category now
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    cafe: Mapped["Cafe"] = relationship("Cafe", back_populates="menu_items")
    options: Mapped[list["MenuItemOption"]] = relationship(
        "MenuItemOption",
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )


class MenuItemOption(Base):
    """Options for menu items (e.g., size, spice level, toppings)."""

    __tablename__ = "menu_item_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    menu_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Размер порции"
    values: Mapped[list[str]] = mapped_column(JSON, nullable=False)  # e.g., ["Стандарт", "Большая"]
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="options")


class CafeLinkRequest(Base, TimestampMixin):
    """
    Model for cafe link requests to Telegram.
    Stores requests from cafe owners to link their Telegram account to a cafe for notifications.
    """

    __tablename__ = "cafe_link_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafes.id"), nullable=False)
    tg_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tg_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[LinkRequestStatus] = mapped_column(String(20), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    cafe: Mapped["Cafe"] = relationship("Cafe", back_populates="link_requests")
