"""Entidades de cuenta gestionada y su perfil (modelos de negocio puros)."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from .enums import AccountStatus, Platform


class ProfileEntity(BaseModel):
    """Datos personales asociados a una cuenta (relación 1-1)."""
    id: UUID | None = None
    account_id: UUID | None = None
    full_name: str | None = None
    phone: str | None = None
    birth_date: date | None = None
    x_username: str | None = None
    fb_username: str | None = None


class AccountEntity(BaseModel):
    """Cuenta gestionada. `encrypted_password` guarda SIEMPRE el valor cifrado."""
    id: UUID | None = None
    platform: Platform
    email: EmailStr
    encrypted_password: str
    recovery_email: EmailStr | None = None
    status: AccountStatus = AccountStatus.active
    notes: str | None = None
    server_id: UUID | None = None
    batch_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    profile: ProfileEntity | None = None
