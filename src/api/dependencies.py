"""Proveedores de dependencias (Depends) para routers, servicios y casos de uso."""
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import Client

from ..core.config import Settings, get_settings
from ..domain.exceptions import AuthorizationError
from ..domain.interfaces.repositories import (
    IAccountRepository,
    IAuditRepository,
    IStatsRepository,
    IUserRepository,
)
from ..domain.interfaces.services import IAuthService, IEncryptionService
from ..domain.usecases.accounts import (
    BulkCreateAccountsUseCase,
    CreateAccountUseCase,
    DeleteAccountUseCase,
    GetAccountsUseCase,
    GetAccountUseCase,
    UpdateAccountUseCase,
    UpdateStatusUseCase,
)
from ..domain.usecases.admin import (
    CreateOperatorUseCase,
    DeleteOperatorUseCase,
    GetAdminStatsUseCase,
    GetRecentAuditUseCase,
    ListOperatorsUseCase,
)
from ..domain.usecases.auth import LoginUseCase
from ..infrastructure.repositories.supabase_account_repository import (
    SupabaseAccountRepository,
)
from ..infrastructure.repositories.supabase_audit_repository import (
    SupabaseAuditRepository,
)
from ..infrastructure.repositories.supabase_stats_repository import (
    SupabaseStatsRepository,
)
from ..infrastructure.repositories.supabase_user_repository import SupabaseUserRepository
from ..infrastructure.services.auth_service import AuthService
from ..infrastructure.services.encryption_service import FernetEncryptionService
from ..infrastructure.services.supabase_client import get_supabase_client

SettingsDep = Annotated[Settings, Depends(get_settings)]


# ---------- Infraestructura ----------
def get_client() -> Client:
    return get_supabase_client()


ClientDep = Annotated[Client, Depends(get_client)]


def get_encryption_service(settings: SettingsDep) -> IEncryptionService:
    return FernetEncryptionService(settings.fernet_key)


def get_auth_service(settings: SettingsDep) -> IAuthService:
    return AuthService(
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.access_token_expire_minutes,
    )


EncryptionDep = Annotated[IEncryptionService, Depends(get_encryption_service)]
AuthServiceDep = Annotated[IAuthService, Depends(get_auth_service)]


# ---------- Repositorios ----------
def get_user_repository(client: ClientDep) -> IUserRepository:
    return SupabaseUserRepository(client)


def get_account_repository(client: ClientDep) -> IAccountRepository:
    return SupabaseAccountRepository(client)


def get_audit_repository(client: ClientDep) -> IAuditRepository:
    return SupabaseAuditRepository(client)


def get_stats_repository(client: ClientDep) -> IStatsRepository:
    return SupabaseStatsRepository(client)


UserRepoDep = Annotated[IUserRepository, Depends(get_user_repository)]
AccountRepoDep = Annotated[IAccountRepository, Depends(get_account_repository)]
AuditRepoDep = Annotated[IAuditRepository, Depends(get_audit_repository)]
StatsRepoDep = Annotated[IStatsRepository, Depends(get_stats_repository)]


# ---------- Autenticación del request ----------
class CurrentUser(BaseModel):
    id: UUID
    email: str
    role: str


_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    auth: AuthServiceDep,
) -> CurrentUser:
    payload = auth.decode_token(credentials.credentials)
    return CurrentUser(id=payload["sub"], email=payload.get("email", ""), role=payload.get("role", ""))


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_role(allowed: list[str]):
    """Fábrica de dependencias que exige que el usuario tenga uno de los roles dados."""

    def checker(user: CurrentUserDep) -> CurrentUser:
        if user.role not in allowed:
            raise AuthorizationError(
                f"Se requiere uno de los roles {allowed}; el usuario es '{user.role}'"
            )
        return user

    return checker


# Cuentas: admin y operator. Admin: solo admin.
AccountUserDep = Annotated[CurrentUser, Depends(require_role(["admin", "operator"]))]
AdminUserDep = Annotated[CurrentUser, Depends(require_role(["admin"]))]


# ---------- Casos de uso ----------
def get_login_usecase(users: UserRepoDep, auth: AuthServiceDep) -> LoginUseCase:
    return LoginUseCase(users, auth)


def get_list_accounts_usecase(accounts: AccountRepoDep) -> GetAccountsUseCase:
    return GetAccountsUseCase(accounts)


def get_account_usecase(
    accounts: AccountRepoDep, audit: AuditRepoDep
) -> GetAccountUseCase:
    return GetAccountUseCase(accounts, audit)


def get_create_account_usecase(
    accounts: AccountRepoDep, encryption: EncryptionDep, audit: AuditRepoDep
) -> CreateAccountUseCase:
    return CreateAccountUseCase(accounts, encryption, audit)


def get_update_account_usecase(
    accounts: AccountRepoDep, encryption: EncryptionDep, audit: AuditRepoDep
) -> UpdateAccountUseCase:
    return UpdateAccountUseCase(accounts, encryption, audit)


def get_update_status_usecase(
    accounts: AccountRepoDep, audit: AuditRepoDep
) -> UpdateStatusUseCase:
    return UpdateStatusUseCase(accounts, audit)


def get_bulk_create_usecase(
    accounts: AccountRepoDep, encryption: EncryptionDep, audit: AuditRepoDep
) -> BulkCreateAccountsUseCase:
    return BulkCreateAccountsUseCase(accounts, encryption, audit)


def get_delete_account_usecase(
    accounts: AccountRepoDep, audit: AuditRepoDep
) -> DeleteAccountUseCase:
    return DeleteAccountUseCase(accounts, audit)


# ---------- Casos de uso de admin ----------
def get_admin_stats_usecase(stats: StatsRepoDep) -> GetAdminStatsUseCase:
    return GetAdminStatsUseCase(stats)


def get_recent_audit_usecase(audit: AuditRepoDep) -> GetRecentAuditUseCase:
    return GetRecentAuditUseCase(audit)


def get_list_operators_usecase(users: UserRepoDep) -> ListOperatorsUseCase:
    return ListOperatorsUseCase(users)


def get_create_operator_usecase(
    users: UserRepoDep, auth: AuthServiceDep
) -> CreateOperatorUseCase:
    return CreateOperatorUseCase(users, auth)


def get_delete_operator_usecase(users: UserRepoDep) -> DeleteOperatorUseCase:
    return DeleteOperatorUseCase(users)
