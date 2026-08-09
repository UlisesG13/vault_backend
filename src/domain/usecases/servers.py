"""Casos de uso sobre servidores/dispositivos (solo rol admin)."""
from typing import Any
from uuid import UUID

from ..entities.server import ServerEntity
from ..exceptions import DuplicateError, NotFoundError
from ..interfaces.repositories import IServerRepository


class ListServersUseCase:
    def __init__(self, servers: IServerRepository) -> None:
        self._servers = servers

    def execute(self) -> list[ServerEntity]:
        return self._servers.list()


class GetServerUseCase:
    def __init__(self, servers: IServerRepository) -> None:
        self._servers = servers

    def execute(self, server_id: UUID) -> ServerEntity:
        server = self._servers.get(server_id)
        if server is None:
            raise NotFoundError(f"No existe el servidor {server_id}")
        return server


class CreateServerUseCase:
    def __init__(self, servers: IServerRepository) -> None:
        self._servers = servers

    def execute(self, server: ServerEntity) -> ServerEntity:
        if self._servers.get_by_name(server.name) is not None:
            raise DuplicateError(f"Ya existe un servidor llamado '{server.name}'")
        return self._servers.create(server)


class UpdateServerUseCase:
    def __init__(self, servers: IServerRepository) -> None:
        self._servers = servers

    def execute(self, server_id: UUID, fields: dict[str, Any]) -> ServerEntity:
        if self._servers.get(server_id) is None:
            raise NotFoundError(f"No existe el servidor {server_id}")
        new_name = fields.get("name")
        if new_name:
            existing = self._servers.get_by_name(new_name)
            if existing is not None and existing.id != server_id:
                raise DuplicateError(f"Ya existe un servidor llamado '{new_name}'")
        return self._servers.update(server_id, fields)


class DeleteServerUseCase:
    def __init__(self, servers: IServerRepository) -> None:
        self._servers = servers

    def execute(self, server_id: UUID) -> None:
        if self._servers.get(server_id) is None:
            raise NotFoundError(f"No existe el servidor {server_id}")
        # Las cuentas apuntando a este servidor quedan con server_id = NULL (ON DELETE SET NULL).
        self._servers.delete(server_id)
