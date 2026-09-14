from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetBase(BaseModel):
    category_id: int | None = None
    limit_amount: Decimal = Field(..., gt=0, decimal_places=2)
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000, le=2100)


class BudgetCreate(BudgetBase):
    pass


class BudgetRead(BudgetBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetStatus(BaseModel):
    budget_id: int
    category_id: int | None
    limit_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    usage_percent: float
    month: int
    year: int
    is_exceeded: bool
