"""Contratos abstractos de los repositorios (puertos de la arquitectura)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from ..entities.account import AccountEntity, ProfileEntity
from ..entities.enums import AccountStatus
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
        skip: int = 0,
        limit: int = 50,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> list[AccountEntity]: ...

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
    def bulk_create(self, accounts: list[tuple[AccountEntity, ProfileEntity]]) -> int: ...

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
