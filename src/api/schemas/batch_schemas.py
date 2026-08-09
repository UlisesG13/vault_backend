"""DTOs de lotes de cuentas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from ...domain.entities.batch import BatchEntity


class BatchCreate(BaseModel):
    name: str
    purchase_date: date | None = None
    notes: str | None = None


class BatchResponse(BaseModel):
    id: UUID
    name: str
    purchase_date: date | None = None
    notes: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_entity(cls, batch: BatchEntity) -> "BatchResponse":
        return cls(
            id=batch.id,  # type: ignore[arg-type]
            name=batch.name,
            purchase_date=batch.purchase_date,
            notes=batch.notes,
            created_at=batch.created_at,
        )
