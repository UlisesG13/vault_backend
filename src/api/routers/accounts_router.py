"""Endpoints de gestión de cuentas (roles: admin y operator)."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status as http_status

from ...domain.entities.account import AccountEntity, ProfileEntity
from ...domain.entities.enums import AccountStatus, Platform, UserRole
from ...domain.usecases.accounts import (
    BulkCreateAccountsUseCase,
    CreateAccountUseCase,
    DeleteAccountUseCase,
    GetAccountsUseCase,
    GetAccountUseCase,
    UpdateAccountUseCase,
    UpdateStatusUseCase,
)
from ...domain.usecases.imports import ImportAccountsUseCase
from ..dependencies import (
    AccountUserDep,
    AdminUserDep,
    EncryptionDep,
    get_account_usecase,
    get_bulk_create_usecase,
    get_create_account_usecase,
    get_delete_account_usecase,
    get_import_accounts_usecase,
    get_list_accounts_usecase,
    get_update_account_usecase,
    get_update_status_usecase,
)
from ..schemas.account_schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    BulkAccountsRequest,
    BulkResult,
    StatusUpdate,
)
from ..schemas.assignment_schemas import ImportResult

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

_ACCOUNT_KEYS = {"platform", "email", "recovery_email", "status", "notes", "server_id", "batch_id"}
_PROFILE_KEYS = {"full_name", "phone", "birth_date", "x_username", "fb_username"}


def _to_response(account: AccountEntity, encryption: EncryptionDep) -> AccountResponse:
    """Construye la respuesta descifrando la contraseña (ambos roles la ven)."""
    return AccountResponse.from_entity(account, encryption.decrypt(account.encrypted_password))


def _split_create(body: AccountCreate) -> tuple[AccountEntity, ProfileEntity]:
    account = AccountEntity(
        platform=body.platform,
        email=body.email,
        encrypted_password="",  # lo asigna el caso de uso tras cifrar
        recovery_email=body.recovery_email,
        status=body.status,
        notes=body.notes,
        server_id=body.server_id,
        batch_id=body.batch_id,
    )
    profile = ProfileEntity(
        full_name=body.full_name,
        phone=body.phone,
        birth_date=body.birth_date,
        x_username=body.x_username,
        fb_username=body.fb_username,
    )
    return account, profile


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    current_user: AccountUserDep,
    encryption: EncryptionDep,
    usecase: Annotated[GetAccountsUseCase, Depends(get_list_accounts_usecase)],
    status: AccountStatus | None = None,
    platform: Platform | None = None,
    search: str | None = None,
    server_id: UUID | None = None,
    batch_id: UUID | None = None,
    assigned_to: UUID | None = None,
    unassigned: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    order_by: str = "created_at",
    descending: bool = True,
) -> list[AccountResponse]:
    # Los operadores solo ven sus cuentas asignadas; ignoran filtros de asignación ajenos.
    if current_user.role == UserRole.operator:
        assigned_to = current_user.id
        unassigned = False
    accounts = usecase.execute(
        status=status.value if status else None,
        platform=platform.value if platform else None,
        search=search,
        server_id=server_id,
        batch_id=batch_id,
        assigned_to=assigned_to,
        unassigned=unassigned,
        skip=skip,
        limit=limit,
        order_by=order_by,
        descending=descending,
    )
    return [_to_response(a, encryption) for a in accounts]


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: UUID,
    current_user: AccountUserDep,
    encryption: EncryptionDep,
    usecase: Annotated[GetAccountUseCase, Depends(get_account_usecase)],
) -> AccountResponse:
    account = usecase.execute(account_id, actor_id=current_user.id)
    return _to_response(account, encryption)


@router.post("", response_model=AccountResponse, status_code=http_status.HTTP_201_CREATED)
def create_account(
    body: AccountCreate,
    current_user: AccountUserDep,
    encryption: EncryptionDep,
    usecase: Annotated[CreateAccountUseCase, Depends(get_create_account_usecase)],
) -> AccountResponse:
    account, profile = _split_create(body)
    created = usecase.execute(account, profile, body.password, actor_id=current_user.id)
    return _to_response(created, encryption)


@router.patch("/{account_id}/status", response_model=AccountResponse)
def update_status(
    account_id: UUID,
    body: StatusUpdate,
    current_user: AccountUserDep,
    encryption: EncryptionDep,
    usecase: Annotated[UpdateStatusUseCase, Depends(get_update_status_usecase)],
) -> AccountResponse:
    updated = usecase.execute(account_id, body.status, actor_id=current_user.id)
    return _to_response(updated, encryption)


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: UUID,
    body: AccountUpdate,
    current_user: AccountUserDep,
    encryption: EncryptionDep,
    usecase: Annotated[UpdateAccountUseCase, Depends(get_update_account_usecase)],
) -> AccountResponse:
    data = body.model_dump(exclude_unset=True, mode="json")
    new_password = data.pop("password", None)
    account_fields = {k: v for k, v in data.items() if k in _ACCOUNT_KEYS}
    profile_fields = {k: v for k, v in data.items() if k in _PROFILE_KEYS}
    updated = usecase.execute(
        account_id, account_fields, profile_fields, new_password, actor_id=current_user.id
    )
    return _to_response(updated, encryption)


@router.post("/bulk", response_model=BulkResult)
def bulk_create(
    body: BulkAccountsRequest,
    current_user: AccountUserDep,
    usecase: Annotated[BulkCreateAccountsUseCase, Depends(get_bulk_create_usecase)],
) -> BulkResult:
    items = []
    for item in body.accounts:
        account, profile = _split_create(item)
        items.append((account, profile, item.password))
    result = usecase.execute(items, actor_id=current_user.id)
    return BulkResult(**result)


@router.post("/import", response_model=ImportResult)
async def import_accounts(
    current_user: AdminUserDep,
    usecase: Annotated[ImportAccountsUseCase, Depends(get_import_accounts_usecase)],
    server_id: Annotated[UUID, Form()],
    batch_id: Annotated[UUID, Form()],
    file: Annotated[UploadFile, File()],
    operator_id: Annotated[UUID | None, Form()] = None,
) -> ImportResult:
    """Importación inteligente (SOLO admin): crea cuentas desde un CSV/Excel
    asociando servidor, lote y (opcional) operador en un solo paso."""
    content = await file.read()
    result = usecase.execute(
        content=content,
        filename=file.filename or "",
        server_id=server_id,
        batch_id=batch_id,
        operator_id=operator_id,
        actor_id=current_user.id,
    )
    return ImportResult(**result)


@router.delete("/{account_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    current_user: AccountUserDep,
    usecase: Annotated[DeleteAccountUseCase, Depends(get_delete_account_usecase)],
) -> None:
    usecase.execute(account_id, actor_id=current_user.id)
