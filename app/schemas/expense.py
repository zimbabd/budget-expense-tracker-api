from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExpenseBase(BaseModel):
    category_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: str | None = Field(None, max_length=255)
    expense_date: date
    is_recurring: bool = False


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    description: str | None = Field(None, max_length=255)
    expense_date: date | None = None
    is_recurring: bool | None = None


class ExpenseRead(ExpenseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExpenseReadWithWarning(ExpenseRead):
    budget_warning: str | None = None


class ExpenseSummary(BaseModel):
    category_id: int
    category_name: str
    total_amount: Decimal
    expense_count: int
    month: int
    year: int
