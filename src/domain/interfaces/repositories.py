"""Contratos abstractos de los repositorios (puertos de la arquitectura)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from ..entities.account import AccountEntity, ProfileEntity
from ..entities.assignment import AssignmentEntity
from ..entities.batch import BatchEntity
from ..entities.enums import AccountStatus
from ..entities.expense import ExpenseEntity
from ..entities.server import ServerEntity
from ..entities.user import UserEntity


class IUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> UserEntity | None: ...

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> UserEntity | None: ...

    @abstractmethod
    def list_by_role(self, role: str) -> list[UserEntity]: ...

    @abstractmethod
    def create(self, email: str, hashed_password: str, role: str) -> UserEntity: ...

    @abstractmethod
    def delete(self, user_id: UUID) -> None: ...


class IAccountRepository(ABC):
    @abstractmethod
    def list(
        self,
        *,
        status: str | None = None,
        platform: str | None = None,
        search: str | None = None,
        server_id: UUID | None = None,
        batch_id: UUID | None = None,
        assigned_to: UUID | None = None,
        unassigned: bool = False,
        skip: int = 0,
        limit: int = 50,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> list[AccountEntity]: ...

    @abstractmethod
    def list_ids_by_batch(self, batch_id: UUID) -> list[UUID]: ...

    @abstractmethod
    def list_by_ids(self, account_ids: list[UUID]) -> list[AccountEntity]:
        """Devuelve las cuentas existentes cuyo id está en la lista (sin orden garantizado)."""
        ...

    @abstractmethod
    def bulk_update_server(self, account_ids: list[UUID], server_id: UUID) -> int:
        """Asigna account_ids a server_id en una sola UPDATE. Devuelve las filas afectadas."""
        ...

    @abstractmethod
    def get(self, account_id: UUID) -> AccountEntity | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> AccountEntity | None: ...

    @abstractmethod
    def create(self, account: AccountEntity, profile: ProfileEntity) -> AccountEntity: ...

    @abstractmethod
    def update(
        self,
        account_id: UUID,
        account_fields: dict[str, Any],
        profile_fields: dict[str, Any],
    ) -> AccountEntity: ...

    @abstractmethod
    def update_status(self, account_id: UUID, status: AccountStatus) -> AccountEntity: ...

    @abstractmethod
    def bulk_create(
        self, accounts: list[tuple[AccountEntity, ProfileEntity]]
    ) -> list[UUID]:
        """Inserta las cuentas y devuelve los IDs creados (en el mismo orden)."""
        ...

    @abstractmethod
    def delete(self, account_id: UUID) -> None: ...


class IAuditRepository(ABC):
    @abstractmethod
    def log(
        self,
        *,
        action: str,
        account_id: UUID | None = None,
        system_user_id: UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> None: ...

    @abstractmethod
    def list_recent(self, limit: int) -> list[dict[str, Any]]:
        """Devuelve las últimas entradas de auditoría enriquecidas con
        email del usuario que actuó y del correo de la cuenta afectada."""
        ...


class IStatsRepository(ABC):
    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Devuelve estadísticas agregadas de las cuentas gestionadas."""
        ...


class IServerRepository(ABC):
    @abstractmethod
    def list(self) -> list[ServerEntity]: ...

    @abstractmethod
    def get(self, server_id: UUID) -> ServerEntity | None: ...

    @abstractmethod
    def get_by_name(self, name: str) -> ServerEntity | None: ...

    @abstractmethod
    def create(self, server: ServerEntity) -> ServerEntity: ...

    @abstractmethod
    def update(self, server_id: UUID, fields: dict[str, Any]) -> ServerEntity: ...

    @abstractmethod
    def delete(self, server_id: UUID) -> None: ...


class IBatchRepository(ABC):
    @abstractmethod
    def list(self) -> list[BatchEntity]: ...

    @abstractmethod
    def get(self, batch_id: UUID) -> BatchEntity | None: ...

    @abstractmethod
    def create(self, batch: BatchEntity) -> BatchEntity: ...

    @abstractmethod
    def delete(self, batch_id: UUID) -> None: ...


class IExpenseRepository(ABC):
    @abstractmethod
    def list(self, batch_id: UUID | None = None) -> list[ExpenseEntity]: ...

    @abstractmethod
    def get(self, expense_id: UUID) -> ExpenseEntity | None: ...

    @abstractmethod
    def create(self, expense: ExpenseEntity) -> ExpenseEntity: ...

    @abstractmethod
    def update(self, expense_id: UUID, fields: dict[str, Any]) -> ExpenseEntity: ...

    @abstractmethod
    def delete(self, expense_id: UUID) -> None: ...


class IAssignmentRepository(ABC):
    @abstractmethod
    def bulk_assign(
        self, account_ids: list[UUID], user_id: UUID, assigned_by: UUID | None
    ) -> int:
        """Asigna varias cuentas a un usuario ignorando duplicados. Devuelve cuántas filas insertó."""
        ...

    @abstractmethod
    def list_by_user(self, user_id: UUID) -> list[AssignmentEntity]: ...

    @abstractmethod
    def list_by_account(self, account_id: UUID) -> list[AssignmentEntity]: ...

    @abstractmethod
    def list_assigned_account_ids(self) -> list[UUID]:
        """Todos los account_id con al menos una asignación (sin duplicados)."""
        ...

    @abstractmethod
    def unassign(self, account_id: UUID, user_id: UUID) -> None: ...
