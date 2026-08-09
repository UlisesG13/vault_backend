"""DTOs de asignaciones e importación."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, model_validator

from ...domain.entities.assignment import AssignmentEntity


class AssignRequest(BaseModel):
    """Asigna cuentas a un operador por lista de IDs, por lote entero, o ambos."""
    user_id: UUID
    account_ids: list[UUID] | None = None
    batch_id: UUID | None = None

    @model_validator(mode="after")
    def _at_least_one_source(self) -> "AssignRequest":
        if not self.account_ids and self.batch_id is None:
            raise ValueError("Debes indicar 'account_ids' o 'batch_id'")
        return self


class AssignResult(BaseModel):
    assigned: int
    requested: int


class UnassignRequest(BaseModel):
    account_id: UUID
    user_id: UUID


class AssignmentResponse(BaseModel):
    id: UUID
    account_id: UUID
    user_id: UUID
    assigned_by: UUID | None = None
    assigned_at: datetime | None = None

    @classmethod
    def from_entity(cls, a: AssignmentEntity) -> "AssignmentResponse":
        return cls(
            id=a.id,  # type: ignore[arg-type]
            account_id=a.account_id,
            user_id=a.user_id,
            assigned_by=a.assigned_by,
            assigned_at=a.assigned_at,
        )


class RowError(BaseModel):
    row: int
    reason: str


class ImportResult(BaseModel):
    inserted: int
    skipped: int
    assigned: int
    skipped_emails: list[str]
    row_errors: list[RowError]
