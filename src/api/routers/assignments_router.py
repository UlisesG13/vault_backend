"""Endpoints de asignación de cuentas a operadores (SOLO rol admin)."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status as http_status

from ...domain.usecases.assignments import (
    AssignAccountsUseCase,
    ListUserAssignmentsUseCase,
    UnassignAccountUseCase,
)
from ..dependencies import (
    AdminUserDep,
    get_assign_accounts_usecase,
    get_list_user_assignments_usecase,
    get_unassign_account_usecase,
    require_role,
)
from ..schemas.assignment_schemas import (
    AssignmentResponse,
    AssignRequest,
    AssignResult,
    UnassignRequest,
)

router = APIRouter(
    prefix="/api/assignments",
    tags=["assignments"],
    dependencies=[Depends(require_role(["admin"]))],
)


@router.post("", response_model=AssignResult)
def assign_accounts(
    body: AssignRequest,
    current_user: AdminUserDep,
    usecase: Annotated[AssignAccountsUseCase, Depends(get_assign_accounts_usecase)],
) -> AssignResult:
    result = usecase.execute(
        user_id=body.user_id,
        account_ids=body.account_ids,
        batch_id=body.batch_id,
        actor_id=current_user.id,
    )
    return AssignResult(**result)


@router.get("/user/{user_id}", response_model=list[AssignmentResponse])
def list_user_assignments(
    user_id: UUID,
    usecase: Annotated[
        ListUserAssignmentsUseCase, Depends(get_list_user_assignments_usecase)
    ],
) -> list[AssignmentResponse]:
    return [AssignmentResponse.from_entity(a) for a in usecase.execute(user_id)]


@router.delete("", status_code=http_status.HTTP_204_NO_CONTENT)
def unassign_account(
    body: UnassignRequest,
    current_user: AdminUserDep,
    usecase: Annotated[UnassignAccountUseCase, Depends(get_unassign_account_usecase)],
) -> None:
    usecase.execute(body.account_id, body.user_id, actor_id=current_user.id)
