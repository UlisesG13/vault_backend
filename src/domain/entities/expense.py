"""Entidad de gasto (modelo de negocio puro). Replica la pestaña 'gastos polllitos'."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ExpenseEntity(BaseModel):
    """Gasto asociado (opcionalmente) a un lote de cuentas."""
    id: UUID | None = None
    batch_id: UUID | None = None
    amount: Decimal
    expense_date: date | None = None
    account_quantity: int = 0
    description: str | None = None
    created_at: datetime | None = None
