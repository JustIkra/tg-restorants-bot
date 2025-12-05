from decimal import Decimal

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Cafe(Base, TimestampMixin):
    __tablename__ = "cafes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    combos: Mapped[list["Combo"]] = relationship("Combo", back_populates="cafe")
    menu_items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="cafe")
    deadlines: Mapped[list["Deadline"]] = relationship("Deadline", back_populates="cafe")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="cafe")
    summaries: Mapped[list["Summary"]] = relationship("Summary", back_populates="cafe")


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
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # only for extras
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    cafe: Mapped["Cafe"] = relationship("Cafe", back_populates="menu_items")
