"""Casos de uso sobre gastos ('gastos polllitos'). Solo rol admin."""
from typing import Any
from uuid import UUID

from ..entities.expense import ExpenseEntity
from ..exceptions import NotFoundError
from ..interfaces.repositories import IBatchRepository, IExpenseRepository


class ListExpensesUseCase:
    def __init__(self, expenses: IExpenseRepository) -> None:
        self._expenses = expenses

    def execute(self, batch_id: UUID | None = None) -> list[ExpenseEntity]:
        return self._expenses.list(batch_id)


class CreateExpenseUseCase:
    def __init__(self, expenses: IExpenseRepository, batches: IBatchRepository) -> None:
        self._expenses = expenses
        self._batches = batches

    def execute(self, expense: ExpenseEntity) -> ExpenseEntity:
        if expense.batch_id is not None and self._batches.get(expense.batch_id) is None:
            raise NotFoundError(f"No existe el lote {expense.batch_id}")
        return self._expenses.create(expense)


class UpdateExpenseUseCase:
    def __init__(self, expenses: IExpenseRepository, batches: IBatchRepository) -> None:
        self._expenses = expenses
        self._batches = batches

    def execute(self, expense_id: UUID, fields: dict[str, Any]) -> ExpenseEntity:
        if self._expenses.get(expense_id) is None:
            raise NotFoundError(f"No existe el gasto {expense_id}")
        new_batch_id = fields.get("batch_id")
        if new_batch_id is not None and self._batches.get(new_batch_id) is None:
            raise NotFoundError(f"No existe el lote {new_batch_id}")
        return self._expenses.update(expense_id, fields)


class DeleteExpenseUseCase:
    def __init__(self, expenses: IExpenseRepository) -> None:
        self._expenses = expenses

    def execute(self, expense_id: UUID) -> None:
        if self._expenses.get(expense_id) is None:
            raise NotFoundError(f"No existe el gasto {expense_id}")
        self._expenses.delete(expense_id)
