"""Endpoints de gastos ('gastos polllitos'). SOLO rol admin."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status as http_status

from ...domain.entities.expense import ExpenseEntity
from ...domain.usecases.expenses import (
    CreateExpenseUseCase,
    DeleteExpenseUseCase,
    ListExpensesUseCase,
    UpdateExpenseUseCase,
)
from ..dependencies import (
    get_create_expense_usecase,
    get_delete_expense_usecase,
    get_list_expenses_usecase,
    get_update_expense_usecase,
    require_role,
)
from ..schemas.expense_schemas import ExpenseCreate, ExpenseResponse, ExpenseUpdate

router = APIRouter(
    prefix="/api/expenses",
    tags=["expenses"],
    dependencies=[Depends(require_role(["admin"]))],
)


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    usecase: Annotated[ListExpensesUseCase, Depends(get_list_expenses_usecase)],
    batch_id: UUID | None = Query(None),
) -> list[ExpenseResponse]:
    return [ExpenseResponse.from_entity(e) for e in usecase.execute(batch_id)]


@router.post("", response_model=ExpenseResponse, status_code=http_status.HTTP_201_CREATED)
def create_expense(
    body: ExpenseCreate,
    usecase: Annotated[CreateExpenseUseCase, Depends(get_create_expense_usecase)],
) -> ExpenseResponse:
    expense = ExpenseEntity(
        batch_id=body.batch_id,
        amount=body.amount,
        expense_date=body.expense_date,
        account_quantity=body.account_quantity,
        description=body.description,
    )
    return ExpenseResponse.from_entity(usecase.execute(expense))


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: UUID,
    body: ExpenseUpdate,
    usecase: Annotated[UpdateExpenseUseCase, Depends(get_update_expense_usecase)],
) -> ExpenseResponse:
    fields = body.model_dump(exclude_unset=True, mode="json")
    return ExpenseResponse.from_entity(usecase.execute(expense_id, fields))


@router.delete("/{expense_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: UUID,
    usecase: Annotated[DeleteExpenseUseCase, Depends(get_delete_expense_usecase)],
) -> None:
    usecase.execute(expense_id)
