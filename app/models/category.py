from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint(
        "user_id", "name", name="uq_user_category_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="categories")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="category")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="category")
