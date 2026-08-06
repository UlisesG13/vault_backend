"""Casos de uso del panel de administración (solo rol admin)."""
from typing import Any
from uuid import UUID

from ..entities.enums import UserRole
from ..entities.user import UserEntity
from ..exceptions import AuthorizationError, DuplicateEmailError, NotFoundError
from ..interfaces.repositories import IAuditRepository, IStatsRepository, IUserRepository
from ..interfaces.services import IAuthService


class GetAdminStatsUseCase:
    def __init__(self, stats: IStatsRepository) -> None:
        self._stats = stats

    def execute(self) -> dict[str, Any]:
        return self._stats.get_stats()


class GetRecentAuditUseCase:
    def __init__(self, audit: IAuditRepository) -> None:
        self._audit = audit

    def execute(self, limit: int) -> list[dict[str, Any]]:
        return self._audit.list_recent(limit)


class ListOperatorsUseCase:
    def __init__(self, users: IUserRepository) -> None:
        self._users = users

    def execute(self) -> list[UserEntity]:
        return self._users.list_by_role(UserRole.operator.value)


class CreateOperatorUseCase:
    def __init__(self, users: IUserRepository, auth: IAuthService) -> None:
        self._users = users
        self._auth = auth

    def execute(self, email: str, password: str) -> UserEntity:
        if self._users.get_by_email(email) is not None:
            raise DuplicateEmailError(f"Ya existe un usuario con el correo {email}")
        hashed = self._auth.hash_password(password)
        return self._users.create(email, hashed, UserRole.operator.value)


class DeleteOperatorUseCase:
    def __init__(self, users: IUserRepository) -> None:
        self._users = users

    def execute(self, user_id: UUID) -> None:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"No existe el usuario {user_id}")
        # Regla de negocio: solo se pueden eliminar operadores, nunca administradores.
        if user.role == UserRole.admin:
            raise AuthorizationError("No se puede eliminar a un administrador")
        self._users.delete(user_id)
