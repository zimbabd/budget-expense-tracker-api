from datetime import datetime
from sqlalchemy import Numeric, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "month",
                         "year", name="uq_user_category_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, index=True)
    # category_id = NULL означает общий лимит на месяц по всем категориям.
    # Примечание: MySQL не считает NULL-значения равными в UNIQUE-констрейнте,
    # поэтому уникальность общего лимита (category_id IS NULL) на уровне БД
    # не гарантируется — проверка на дубликат общего лимита делается на уровне
    # бизнес-логики (Шаг 5).
    category_id: Mapped[int | None] = mapped_column(ForeignKey(
        "categories.id", ondelete="CASCADE"), nullable=True, index=True)
    limit_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–12
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="budgets")
    category: Mapped["Category | None"] = relationship(
        back_populates="budgets")
