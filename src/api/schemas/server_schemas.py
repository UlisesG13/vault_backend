"""DTOs de servidores/dispositivos."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ...domain.entities.server import ServerEntity


class ServerCreate(BaseModel):
    name: str
    description: str | None = None


class ServerUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ServerResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_entity(cls, server: ServerEntity) -> "ServerResponse":
        return cls(
            id=server.id,  # type: ignore[arg-type]
            name=server.name,
            description=server.description,
            created_at=server.created_at,
        )
