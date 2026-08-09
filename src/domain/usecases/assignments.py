"""Casos de uso de asignación de cuentas a operadores (solo rol admin)."""
from typing import Any
from uuid import UUID

from ..entities.assignment import AssignmentEntity
from ..entities.enums import UserRole
from ..exceptions import NotFoundError, ValidationError
from ..interfaces.repositories import (
    IAccountRepository,
    IAssignmentRepository,
    IAuditRepository,
    IUserRepository,
)


class AssignAccountsUseCase:
    """Asignación masiva: asigna una lista de cuentas (o un lote entero) a un operador."""

    def __init__(
        self,
        accounts: IAccountRepository,
        users: IUserRepository,
        assignments: IAssignmentRepository,
        audit: IAuditRepository,
    ) -> None:
        self._accounts = accounts
        self._users = users
        self._assignments = assignments
        self._audit = audit

    def execute(
        self,
        user_id: UUID,
        account_ids: list[UUID] | None,
        batch_id: UUID | None,
        actor_id: UUID | None,
    ) -> dict[str, Any]:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"No existe el usuario {user_id}")
        # Regla de negocio: solo se asignan cuentas a operadores, nunca a administradores.
        if user.role == UserRole.admin:
            raise ValidationError("No se pueden asignar cuentas a un administrador")

        ids = list(account_ids or [])
        if batch_id is not None:
            ids.extend(self._accounts.list_ids_by_batch(batch_id))
        # Deduplicar preservando orden.
        ids = list(dict.fromkeys(ids))
        if not ids:
            raise ValidationError("No se indicaron cuentas ni un lote con cuentas para asignar")

        assigned = self._assignments.bulk_assign(ids, user_id, actor_id)
        self._audit.log(
            action="assigned",
            system_user_id=actor_id,
            details={"user_id": str(user_id), "requested": len(ids), "assigned": assigned,
                     "batch_id": str(batch_id) if batch_id else None},
        )
        return {"assigned": assigned, "requested": len(ids)}


class ListUserAssignmentsUseCase:
    def __init__(self, assignments: IAssignmentRepository, users: IUserRepository) -> None:
        self._assignments = assignments
        self._users = users

    def execute(self, user_id: UUID) -> list[AssignmentEntity]:
        if self._users.get_by_id(user_id) is None:
            raise NotFoundError(f"No existe el usuario {user_id}")
        return self._assignments.list_by_user(user_id)


class UnassignAccountUseCase:
    def __init__(
        self, assignments: IAssignmentRepository, audit: IAuditRepository
    ) -> None:
        self._assignments = assignments
        self._audit = audit

    def execute(self, account_id: UUID, user_id: UUID, actor_id: UUID | None) -> None:
        self._assignments.unassign(account_id, user_id)
        self._audit.log(
            action="unassigned",
            account_id=account_id,
            system_user_id=actor_id,
            details={"user_id": str(user_id)},
        )
