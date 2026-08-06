"""Endpoints del panel de administración (SOLO rol admin)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status as http_status
from uuid import UUID

from ...domain.usecases.admin import (
    CreateOperatorUseCase,
    DeleteOperatorUseCase,
    GetAdminStatsUseCase,
    GetRecentAuditUseCase,
    ListOperatorsUseCase,
)
from ..dependencies import (
    get_admin_stats_usecase,
    get_create_operator_usecase,
    get_delete_operator_usecase,
    get_list_operators_usecase,
    get_recent_audit_usecase,
    require_role,
)
from ..schemas.admin_schemas import (
    AuditEntryResponse,
    OperatorCreate,
    OperatorResponse,
    StatsResponse,
)

# require_role(["admin"]) protege TODO el router: ningún operator puede entrar.
router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(["admin"]))],
)


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    usecase: Annotated[GetAdminStatsUseCase, Depends(get_admin_stats_usecase)],
) -> StatsResponse:
    return StatsResponse(**usecase.execute())


@router.get("/audit", response_model=list[AuditEntryResponse])
def get_audit(
    usecase: Annotated[GetRecentAuditUseCase, Depends(get_recent_audit_usecase)],
    limit: int = Query(20, ge=1, le=100),
) -> list[AuditEntryResponse]:
    return [AuditEntryResponse(**entry) for entry in usecase.execute(limit)]


@router.get("/users", response_model=list[OperatorResponse])
def list_operators(
    usecase: Annotated[ListOperatorsUseCase, Depends(get_list_operators_usecase)],
) -> list[OperatorResponse]:
    return [OperatorResponse.from_entity(u) for u in usecase.execute()]


@router.post("/users", response_model=OperatorResponse, status_code=http_status.HTTP_201_CREATED)
def create_operator(
    body: OperatorCreate,
    usecase: Annotated[CreateOperatorUseCase, Depends(get_create_operator_usecase)],
) -> OperatorResponse:
    operator = usecase.execute(body.email, body.password)
    return OperatorResponse.from_entity(operator)


@router.delete("/users/{user_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_operator(
    user_id: UUID,
    usecase: Annotated[DeleteOperatorUseCase, Depends(get_delete_operator_usecase)],
) -> None:
    usecase.execute(user_id)
