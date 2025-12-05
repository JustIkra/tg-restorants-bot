from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Deadline(Base):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafes.id"), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-6 (Monday-Sunday)
    deadline_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM"
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    advance_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    cafe: Mapped["Cafe"] = relationship("Cafe", back_populates="deadlines")
