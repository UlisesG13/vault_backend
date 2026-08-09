"""Endpoints de servidores/dispositivos (SOLO rol admin)."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status as http_status

from ...domain.entities.server import ServerEntity
from ...domain.usecases.servers import (
    CreateServerUseCase,
    DeleteServerUseCase,
    ListServersUseCase,
    UpdateServerUseCase,
)
from ..dependencies import (
    get_create_server_usecase,
    get_delete_server_usecase,
    get_list_servers_usecase,
    get_update_server_usecase,
    require_role,
)
from ..schemas.server_schemas import ServerCreate, ServerResponse, ServerUpdate

router = APIRouter(
    prefix="/api/servers",
    tags=["servers"],
    dependencies=[Depends(require_role(["admin"]))],
)


@router.get("", response_model=list[ServerResponse])
def list_servers(
    usecase: Annotated[ListServersUseCase, Depends(get_list_servers_usecase)],
) -> list[ServerResponse]:
    return [ServerResponse.from_entity(s) for s in usecase.execute()]


@router.post("", response_model=ServerResponse, status_code=http_status.HTTP_201_CREATED)
def create_server(
    body: ServerCreate,
    usecase: Annotated[CreateServerUseCase, Depends(get_create_server_usecase)],
) -> ServerResponse:
    server = ServerEntity(name=body.name, description=body.description)
    return ServerResponse.from_entity(usecase.execute(server))


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: UUID,
    body: ServerUpdate,
    usecase: Annotated[UpdateServerUseCase, Depends(get_update_server_usecase)],
) -> ServerResponse:
    fields = body.model_dump(exclude_unset=True)
    return ServerResponse.from_entity(usecase.execute(server_id, fields))


@router.delete("/{server_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_server(
    server_id: UUID,
    usecase: Annotated[DeleteServerUseCase, Depends(get_delete_server_usecase)],
) -> None:
    usecase.execute(server_id)
