"""Entidad de lote de cuentas (modelo de negocio puro)."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class BatchEntity(BaseModel):
    """Agrupa cuentas compradas/creadas en una fecha (ej. 'correos 6 de agosto')."""
    id: UUID | None = None
    name: str
    purchase_date: date | None = None
    notes: str | None = None
    created_at: datetime | None = None
