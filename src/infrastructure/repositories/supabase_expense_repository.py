"""Repositorio de gastos sobre Supabase."""
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from supabase import Client

from ...domain.entities.expense import ExpenseEntity
from ...domain.interfaces.repositories import IExpenseRepository


def _jsonify(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


class SupabaseExpenseRepository(IExpenseRepository):
    TABLE = "expenses"

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(self, batch_id: UUID | None = None) -> list[ExpenseEntity]:
        query = self._client.table(self.TABLE).select("*")
        if batch_id is not None:
            query = query.eq("batch_id", str(batch_id))
        res = query.order("expense_date", desc=True).execute()
        return [ExpenseEntity(**row) for row in res.data]

    def get(self, expense_id: UUID) -> ExpenseEntity | None:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("id", str(expense_id))
            .limit(1)
            .execute()
        )
        return ExpenseEntity(**res.data[0]) if res.data else None

    def create(self, expense: ExpenseEntity) -> ExpenseEntity:
        row = {
            "batch_id": str(expense.batch_id) if expense.batch_id else None,
            "amount": _jsonify(expense.amount),
            "expense_date": _jsonify(expense.expense_date),
            "account_quantity": expense.account_quantity,
            "description": expense.description,
        }
        # expense_date puede ser None -> deja que la BD ponga current_date.
        row = {k: v for k, v in row.items() if not (k == "expense_date" and v is None)}
        res = self._client.table(self.TABLE).insert(row).execute()
        return ExpenseEntity(**res.data[0])

    def update(self, expense_id: UUID, fields: dict[str, Any]) -> ExpenseEntity:
        payload = {k: _jsonify(v) for k, v in fields.items()}
        self._client.table(self.TABLE).update(payload).eq("id", str(expense_id)).execute()
        updated = self.get(expense_id)
        assert updated is not None
        return updated

    def delete(self, expense_id: UUID) -> None:
        self._client.table(self.TABLE).delete().eq("id", str(expense_id)).execute()
