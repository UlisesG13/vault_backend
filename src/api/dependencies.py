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
    IAssignmentRepository,
    IAuditRepository,
    IBatchRepository,
    IExpenseRepository,
    IServerRepository,
    IStatsRepository,
    IUserRepository,
)
from ..domain.interfaces.services import IAuthService, IEncryptionService, IFileParser
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
from ..domain.usecases.assignments import (
    AssignAccountsUseCase,
    ListUserAssignmentsUseCase,
    UnassignAccountUseCase,
)
from ..domain.usecases.batches import (
    CreateBatchUseCase,
    DeleteBatchUseCase,
    ListBatchesUseCase,
)
from ..domain.usecases.expenses import (
    CreateExpenseUseCase,
    DeleteExpenseUseCase,
    ListExpensesUseCase,
    UpdateExpenseUseCase,
)
from ..domain.usecases.imports import ImportAccountsUseCase
from ..domain.usecases.servers import (
    CreateServerUseCase,
    DeleteServerUseCase,
    GetServerUseCase,
    ListServersUseCase,
    UpdateServerUseCase,
)
from ..infrastructure.repositories.supabase_account_repository import (
    SupabaseAccountRepository,
)
from ..infrastructure.repositories.supabase_assignment_repository import (
    SupabaseAssignmentRepository,
)
from ..infrastructure.repositories.supabase_batch_repository import (
    SupabaseBatchRepository,
)
from ..infrastructure.repositories.supabase_expense_repository import (
    SupabaseExpenseRepository,
)
from ..infrastructure.repositories.supabase_server_repository import (
    SupabaseServerRepository,
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
from ..infrastructure.services.file_parser import FileParserService
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
    return SupabaseAccountRepository(client, SupabaseAssignmentRepository(client))


def get_audit_repository(client: ClientDep) -> IAuditRepository:
    return SupabaseAuditRepository(client)


def get_stats_repository(client: ClientDep) -> IStatsRepository:
    return SupabaseStatsRepository(client)


def get_server_repository(client: ClientDep) -> IServerRepository:
    return SupabaseServerRepository(client)


def get_batch_repository(client: ClientDep) -> IBatchRepository:
    return SupabaseBatchRepository(client)


def get_expense_repository(client: ClientDep) -> IExpenseRepository:
    return SupabaseExpenseRepository(client)


def get_assignment_repository(client: ClientDep) -> IAssignmentRepository:
    return SupabaseAssignmentRepository(client)


def get_file_parser() -> IFileParser:
    return FileParserService()


UserRepoDep = Annotated[IUserRepository, Depends(get_user_repository)]
AccountRepoDep = Annotated[IAccountRepository, Depends(get_account_repository)]
AuditRepoDep = Annotated[IAuditRepository, Depends(get_audit_repository)]
StatsRepoDep = Annotated[IStatsRepository, Depends(get_stats_repository)]
ServerRepoDep = Annotated[IServerRepository, Depends(get_server_repository)]
BatchRepoDep = Annotated[IBatchRepository, Depends(get_batch_repository)]
ExpenseRepoDep = Annotated[IExpenseRepository, Depends(get_expense_repository)]
AssignmentRepoDep = Annotated[IAssignmentRepository, Depends(get_assignment_repository)]
FileParserDep = Annotated[IFileParser, Depends(get_file_parser)]


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


# ---------- Casos de uso: servidores ----------
def get_list_servers_usecase(servers: ServerRepoDep) -> ListServersUseCase:
    return ListServersUseCase(servers)


def get_get_server_usecase(servers: ServerRepoDep) -> GetServerUseCase:
    return GetServerUseCase(servers)


def get_create_server_usecase(servers: ServerRepoDep) -> CreateServerUseCase:
    return CreateServerUseCase(servers)


def get_update_server_usecase(servers: ServerRepoDep) -> UpdateServerUseCase:
    return UpdateServerUseCase(servers)


def get_delete_server_usecase(servers: ServerRepoDep) -> DeleteServerUseCase:
    return DeleteServerUseCase(servers)


# ---------- Casos de uso: lotes ----------
def get_list_batches_usecase(batches: BatchRepoDep) -> ListBatchesUseCase:
    return ListBatchesUseCase(batches)


def get_create_batch_usecase(batches: BatchRepoDep) -> CreateBatchUseCase:
    return CreateBatchUseCase(batches)


def get_delete_batch_usecase(batches: BatchRepoDep) -> DeleteBatchUseCase:
    return DeleteBatchUseCase(batches)


# ---------- Casos de uso: gastos ----------
def get_list_expenses_usecase(expenses: ExpenseRepoDep) -> ListExpensesUseCase:
    return ListExpensesUseCase(expenses)


def get_create_expense_usecase(
    expenses: ExpenseRepoDep, batches: BatchRepoDep
) -> CreateExpenseUseCase:
    return CreateExpenseUseCase(expenses, batches)


def get_update_expense_usecase(
    expenses: ExpenseRepoDep, batches: BatchRepoDep
) -> UpdateExpenseUseCase:
    return UpdateExpenseUseCase(expenses, batches)


def get_delete_expense_usecase(expenses: ExpenseRepoDep) -> DeleteExpenseUseCase:
    return DeleteExpenseUseCase(expenses)


# ---------- Casos de uso: asignaciones e importación ----------
def get_assign_accounts_usecase(
    accounts: AccountRepoDep,
    users: UserRepoDep,
    assignments: AssignmentRepoDep,
    audit: AuditRepoDep,
) -> AssignAccountsUseCase:
    return AssignAccountsUseCase(accounts, users, assignments, audit)


def get_list_user_assignments_usecase(
    assignments: AssignmentRepoDep, users: UserRepoDep
) -> ListUserAssignmentsUseCase:
    return ListUserAssignmentsUseCase(assignments, users)


def get_unassign_account_usecase(
    assignments: AssignmentRepoDep, audit: AuditRepoDep
) -> UnassignAccountUseCase:
    return UnassignAccountUseCase(assignments, audit)


def get_import_accounts_usecase(
    accounts: AccountRepoDep,
    encryption: EncryptionDep,
    assignments: AssignmentRepoDep,
    audit: AuditRepoDep,
    parser: FileParserDep,
    servers: ServerRepoDep,
    batches: BatchRepoDep,
    users: UserRepoDep,
) -> ImportAccountsUseCase:
    return ImportAccountsUseCase(
        accounts, encryption, assignments, audit, parser, servers, batches, users
    )
