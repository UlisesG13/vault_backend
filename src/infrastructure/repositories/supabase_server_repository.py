"""Repositorio de servidores/dispositivos sobre Supabase."""
from typing import Any
from uuid import UUID

from supabase import Client

from ...domain.entities.server import ServerEntity
from ...domain.interfaces.repositories import IServerRepository


class SupabaseServerRepository(IServerRepository):
    TABLE = "servers"

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(self) -> list[ServerEntity]:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return [ServerEntity(**row) for row in res.data]

    def get(self, server_id: UUID) -> ServerEntity | None:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("id", str(server_id))
            .limit(1)
            .execute()
        )
        return ServerEntity(**res.data[0]) if res.data else None

    def get_by_name(self, name: str) -> ServerEntity | None:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("name", name)
            .limit(1)
            .execute()
        )
        return ServerEntity(**res.data[0]) if res.data else None

    def create(self, server: ServerEntity) -> ServerEntity:
        row = {"name": server.name, "description": server.description}
        res = self._client.table(self.TABLE).insert(row).execute()
        return ServerEntity(**res.data[0])

    def update(self, server_id: UUID, fields: dict[str, Any]) -> ServerEntity:
        self._client.table(self.TABLE).update(fields).eq("id", str(server_id)).execute()
        updated = self.get(server_id)
        assert updated is not None
        return updated

    def delete(self, server_id: UUID) -> None:
        self._client.table(self.TABLE).delete().eq("id", str(server_id)).execute()
