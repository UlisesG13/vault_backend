"""Entidad de usuario del sistema (modelo de negocio puro)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from .enums import UserRole


class UserEntity(BaseModel):
    id: UUID
    email: EmailStr
    hashed_password: str
    role: UserRole = UserRole.operator
    created_at: datetime | None = None
