from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    categories: Mapped[list["Category"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan")
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan")
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan")
