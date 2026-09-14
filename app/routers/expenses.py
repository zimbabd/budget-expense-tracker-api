from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.budget import Budget
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseReadWithWarning, ExpenseUpdate
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseReadWithWarning, ExpenseUpdate, ExpenseSummary

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _get_expense_or_404(expense_id: int, user_id: int, db: Session) -> Expense:
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.user_id == user_id)
        .first()
    )
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    return expense


def _validate_category_ownership(
    category_id: int, user_id: int, db: Session
) -> None:
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user_id)
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )


def _check_budget_warning(
    user_id: int,
    category_id: int,
    expense_date: date,
    db: Session,
) -> str | None:
    """Проверяет лимиты бюджета и возвращает предупреждение если превышен."""
    month = expense_date.month
    year = expense_date.year

    # Считаем общую сумму расходов по категории за месяц
    spent = (
        db.query(func.sum(Expense.amount))
        .filter(
            Expense.user_id == user_id,
            Expense.category_id == category_id,
            func.month(Expense.expense_date) == month,
            func.year(Expense.expense_date) == year,
        )
        .scalar() or Decimal("0")
    )

    warnings = []

    # Проверяем лимит по конкретной категории
    category_budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.month == month,
            Budget.year == year,
        )
        .first()
    )
    if category_budget and spent > Decimal(str(category_budget.limit_amount)):
        over = spent - Decimal(str(category_budget.limit_amount))
        warnings.append(
            f"Category budget exceeded by {over:.2f} "
            f"(limit: {category_budget.limit_amount}, spent: {spent:.2f})"
        )

    # Проверяем общий лимит на месяц
    general_budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.category_id.is_(None),
            Budget.month == month,
            Budget.year == year,
        )
        .first()
    )
    if general_budget:
        total_spent = (
            db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                func.month(Expense.expense_date) == month,
                func.year(Expense.expense_date) == year,
            )
            .scalar() or Decimal("0")
        )
        if total_spent > Decimal(str(general_budget.limit_amount)):
            over = total_spent - Decimal(str(general_budget.limit_amount))
            warnings.append(
                f"Monthly budget exceeded by {over:.2f} "
                f"(limit: {general_budget.limit_amount}, spent: {total_spent:.2f})"
            )

    return "; ".join(warnings) if warnings else None


@router.get("/", response_model=list[ExpenseRead])
def list_expenses(
    category_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    is_recurring: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Expense).filter(Expense.user_id == current_user.id)

    if category_id is not None:
        q = q.filter(Expense.category_id == category_id)
    if date_from is not None:
        q = q.filter(Expense.expense_date >= date_from)
    if date_to is not None:
        q = q.filter(Expense.expense_date <= date_to)
    if is_recurring is not None:
        q = q.filter(Expense.is_recurring == is_recurring)

    return q.order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=ExpenseReadWithWarning, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_category_ownership(payload.category_id, current_user.id, db)

    expense = Expense(user_id=current_user.id, **payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)

    warning = _check_budget_warning(
        user_id=current_user.id,
        category_id=expense.category_id,
        expense_date=expense.expense_date,
        db=db,
    )

    return ExpenseReadWithWarning(
        **ExpenseRead.model_validate(expense).model_dump(),
        budget_warning=warning,
    )


@router.get("/summary", response_model=list[ExpenseSummary])
def get_expenses_summary(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Агрегированные расходы по категориям за месяц/год."""
    rows = (
        db.query(
            Expense.category_id,
            Category.name.label("category_name"),
            func.sum(Expense.amount).label("total_amount"),
            func.count(Expense.id).label("expense_count"),
        )
        .join(Category, Expense.category_id == Category.id)
        .filter(
            Expense.user_id == current_user.id,
            func.month(Expense.expense_date) == month,
            func.year(Expense.expense_date) == year,
        )
        .group_by(Expense.category_id, Category.name)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )

    return [
        ExpenseSummary(
            category_id=row.category_id,
            category_name=row.category_name,
            total_amount=Decimal(str(row.total_amount)),
            expense_count=row.expense_count,
            month=month,
            year=year,
        )
        for row in rows
    ]


@router.post("/recurring/generate", response_model=list[ExpenseRead], status_code=status.HTTP_201_CREATED)
def generate_recurring(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Генерирует копии recurring расходов за указанный месяц."""
    # Берём все recurring расходы пользователя
    templates = (
        db.query(Expense)
        .filter(
            Expense.user_id == current_user.id,
            Expense.is_recurring == True,
        )
        .all()
    )

    if not templates:
        return []

    # Проверяем какие уже сгенерированы за этот месяц
    existing = (
        db.query(Expense.category_id, Expense.amount, Expense.description)
        .filter(
            Expense.user_id == current_user.id,
            Expense.is_recurring == True,
            func.month(Expense.expense_date) == month,
            func.year(Expense.expense_date) == year,
        )
        .all()
    )
    existing_set = {(r.category_id, r.amount, r.description) for r in existing}

    # Генерируем только те которых ещё нет
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    new_date = date(year, month, last_day)

    created = []
    for t in templates:
        key = (t.category_id, t.amount, t.description)
        if key in existing_set:
            continue
        new_expense = Expense(
            user_id=current_user.id,
            category_id=t.category_id,
            amount=t.amount,
            description=t.description,
            expense_date=new_date,
            is_recurring=True,
        )
        db.add(new_expense)
        created.append(new_expense)

    db.commit()
    for e in created:
        db.refresh(e)

    return created


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_expense_or_404(expense_id, current_user.id, db)


@router.patch("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = _get_expense_or_404(expense_id, current_user.id, db)
    updates = payload.model_dump(exclude_unset=True)

    if "category_id" in updates and updates["category_id"] is not None:
        _validate_category_ownership(
            updates["category_id"], current_user.id, db)

    for field, value in updates.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = _get_expense_or_404(expense_id, current_user.id, db)
    db.delete(expense)
    db.commit()
