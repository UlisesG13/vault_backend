"""DTOs (Request/Response) de las cuentas gestionadas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from ...domain.entities.account import AccountEntity
from ...domain.entities.enums import AccountStatus, Platform


# ---------- Requests ----------
class AccountCreate(BaseModel):
    platform: Platform
    email: EmailStr
    password: str  # texto plano; se cifra antes de guardar
    recovery_email: EmailStr | None = None
    status: AccountStatus = AccountStatus.active
    notes: str | None = None
    server_id: UUID | None = None
    batch_id: UUID | None = None
    # Datos de perfil (1-1)
    full_name: str | None = None
    phone: str | None = None
    birth_date: date | None = None
    x_username: str | None = None
    fb_username: str | None = None


class AccountUpdate(BaseModel):
    platform: Platform | None = None
    email: EmailStr | None = None
    password: str | None = None
    recovery_email: EmailStr | None = None
    status: AccountStatus | None = None
    notes: str | None = None
    server_id: UUID | None = None
    batch_id: UUID | None = None
    full_name: str | None = None
    phone: str | None = None
    birth_date: date | None = None
    x_username: str | None = None
    fb_username: str | None = None


class StatusUpdate(BaseModel):
    status: AccountStatus


class BulkAccountsRequest(BaseModel):
    accounts: list[AccountCreate]


class BulkResult(BaseModel):
    inserted: int
    skipped: int
    skipped_emails: list[str]


# ---------- Responses ----------
class ProfileResponse(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    birth_date: date | None = None
    x_username: str | None = None
    fb_username: str | None = None


class AccountResponse(BaseModel):
    """Respuesta con la contraseña descifrada. Ambos roles (admin/operator) la ven;
    el frontend la oculta visualmente."""
    id: UUID
    platform: Platform
    email: EmailStr
    password: str
    recovery_email: EmailStr | None = None
    status: AccountStatus
    notes: str | None = None
    server_id: UUID | None = None
    batch_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    profile: ProfileResponse | None = None

    @classmethod
    def from_entity(cls, account: AccountEntity, password: str) -> "AccountResponse":
        profile = (
            ProfileResponse(**account.profile.model_dump(include=set(ProfileResponse.model_fields)))
            if account.profile
            else None
        )
        return cls(
            id=account.id,  # type: ignore[arg-type]
            platform=account.platform,
            email=account.email,
            password=password,
            recovery_email=account.recovery_email,
            status=account.status,
            notes=account.notes,
            server_id=account.server_id,
            batch_id=account.batch_id,
            created_at=account.created_at,
            updated_at=account.updated_at,
            profile=profile,
        )
