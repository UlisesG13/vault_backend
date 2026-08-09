"""Entidad de servidor/dispositivo de origen de las cuentas (modelo de negocio puro)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ServerEntity(BaseModel):
    """Servidor o dispositivo desde donde se crean o corren las cuentas."""
    id: UUID | None = None
    name: str
    description: str | None = None
    created_at: datetime | None = None
