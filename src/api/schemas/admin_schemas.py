"""DTOs del panel de administración."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr

from ...domain.entities.enums import UserRole
from ...domain.entities.user import UserEntity


class OperatorCreate(BaseModel):
    email: EmailStr
    password: str


class OperatorResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
    created_at: datetime | None = None

    @classmethod
    def from_entity(cls, user: UserEntity) -> "OperatorResponse":
        return cls(id=user.id, email=user.email, role=user.role, created_at=user.created_at)


class AuditEntryResponse(BaseModel):
    action: str
    details: dict[str, Any] = {}
    account_id: UUID | None = None
    account_email: EmailStr | None = None
    user_email: EmailStr | None = None
    created_at: datetime | None = None


class TrendPoint(BaseModel):
    date: str
    created: int
    deleted: int


class PlatformDistribution(BaseModel):
    gmail: int
    facebook: int
    twitter: int


class StatsResponse(BaseModel):
    total: int
    active: int
    suspended: int
    banned: int
    created_today: int
    platform_distribution: PlatformDistribution
    trend_last_7_days: list[TrendPoint]
