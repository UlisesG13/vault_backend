"""Entidad de asignación cuenta -> usuario (modelo de negocio puro)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AssignmentEntity(BaseModel):
    """Relación pivote que asigna una cuenta gestionada a un operador."""
    id: UUID | None = None
    account_id: UUID
    user_id: UUID
    assigned_by: UUID | None = None
    assigned_at: datetime | None = None
