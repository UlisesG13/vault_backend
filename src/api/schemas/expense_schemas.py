"""DTOs de gastos."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from ...domain.entities.expense import ExpenseEntity


class ExpenseCreate(BaseModel):
    batch_id: UUID | None = None
    amount: Decimal = Field(ge=0)
    expense_date: date | None = None
    account_quantity: int = Field(default=0, ge=0)
    description: str | None = None


class ExpenseUpdate(BaseModel):
    batch_id: UUID | None = None
    amount: Decimal | None = Field(default=None, ge=0)
    expense_date: date | None = None
    account_quantity: int | None = Field(default=None, ge=0)
    description: str | None = None


class ExpenseResponse(BaseModel):
    id: UUID
    batch_id: UUID | None = None
    amount: Decimal
    expense_date: date | None = None
    account_quantity: int
    description: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_entity(cls, expense: ExpenseEntity) -> "ExpenseResponse":
        return cls(
            id=expense.id,  # type: ignore[arg-type]
            batch_id=expense.batch_id,
            amount=expense.amount,
            expense_date=expense.expense_date,
            account_quantity=expense.account_quantity,
            description=expense.description,
            created_at=expense.created_at,
        )
