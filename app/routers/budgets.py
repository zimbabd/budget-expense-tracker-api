from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.budget import Budget
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetStatus

router = APIRouter(prefix="/budgets", tags=["budgets"])


def _get_budget_or_404(budget_id: int, user_id: int, db: Session) -> Budget:
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.user_id == user_id)
        .first()
    )
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        )
    return budget


def _validate_no_duplicate_budget(
    user_id: int,
    category_id: int | None,
    month: int,
    year: int,
    db: Session,
    exclude_id: int | None = None,
) -> None:
    if category_id is not None:
        q = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.month == month,
            Budget.year == year,
        )
    else:
        q = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.category_id.is_(None),
            Budget.month == month,
            Budget.year == year,
        )

    if exclude_id is not None:
        q = q.filter(Budget.id != exclude_id)

    if q.first():
        label = f"category_id={category_id}" if category_id else "general (no category)"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Budget for {label}, month={month}, year={year} already exists",
        )


@router.get("/status", response_model=list[BudgetStatus])
def get_budgets_status(
    month: int = Query(..., ge=1, le=12, description="Месяц"),
    year: int = Query(..., ge=2000, le=2100, description="Год"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Статус всех лимитов за указанный месяц: потрачено, осталось, процент."""
    budgets = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.month == month,
            Budget.year == year,
        )
        .all()
    )

    result = []
    for budget in budgets:
        if budget.category_id is not None:
            # Расходы по конкретной категории
            spent = (
                db.query(func.sum(Expense.amount))
                .filter(
                    Expense.user_id == current_user.id,
                    Expense.category_id == budget.category_id,
                    func.month(Expense.expense_date) == month,
                    func.year(Expense.expense_date) == year,
                )
                .scalar() or Decimal("0")
            )
        else:
            # Общий лимит — все расходы за месяц
            spent = (
                db.query(func.sum(Expense.amount))
                .filter(
                    Expense.user_id == current_user.id,
                    func.month(Expense.expense_date) == month,
                    func.year(Expense.expense_date) == year,
                )
                .scalar() or Decimal("0")
            )

        spent = Decimal(str(spent))
        limit = Decimal(str(budget.limit_amount))
        remaining = limit - spent
        usage_percent = float(spent / limit * 100) if limit > 0 else 0.0

        result.append(BudgetStatus(
            budget_id=budget.id,
            category_id=budget.category_id,
            limit_amount=limit,
            spent_amount=spent,
            remaining_amount=remaining,
            usage_percent=round(usage_percent, 2),
            month=month,
            year=year,
            is_exceeded=spent > limit,
        ))

    return result


@router.get("/", response_model=list[BudgetRead])
def list_budgets(
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
    category_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Budget).filter(Budget.user_id == current_user.id)

    if month is not None:
        q = q.filter(Budget.month == month)
    if year is not None:
        q = q.filter(Budget.year == year)
    if category_id is not None:
        q = q.filter(Budget.category_id == category_id)

    return q.order_by(Budget.year.desc(), Budget.month.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.category_id is not None:
        category = (
            db.query(Category)
            .filter(
                Category.id == payload.category_id,
                Category.user_id == current_user.id,
            )
            .first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {payload.category_id} not found",
            )

    _validate_no_duplicate_budget(
        user_id=current_user.id,
        category_id=payload.category_id,
        month=payload.month,
        year=payload.year,
        db=db,
    )

    budget = Budget(user_id=current_user.id, **payload.model_dump())
    db.add(budget)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Budget for this period already exists",
        )
    db.refresh(budget)
    return budget


@router.get("/{budget_id}", response_model=BudgetRead)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_budget_or_404(budget_id, current_user.id, db)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = _get_budget_or_404(budget_id, current_user.id, db)
    db.delete(budget)
    db.commit()
