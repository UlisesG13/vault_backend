"""Endpoints de lotes de cuentas (SOLO rol admin)."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status as http_status

from ...domain.entities.batch import BatchEntity
from ...domain.usecases.batches import (
    CreateBatchUseCase,
    DeleteBatchUseCase,
    ListBatchesUseCase,
)
from ..dependencies import (
    get_create_batch_usecase,
    get_delete_batch_usecase,
    get_list_batches_usecase,
    require_role,
)
from ..schemas.batch_schemas import BatchCreate, BatchResponse

router = APIRouter(
    prefix="/api/batches",
    tags=["batches"],
    dependencies=[Depends(require_role(["admin"]))],
)


@router.get("", response_model=list[BatchResponse])
def list_batches(
    usecase: Annotated[ListBatchesUseCase, Depends(get_list_batches_usecase)],
) -> list[BatchResponse]:
    return [BatchResponse.from_entity(b) for b in usecase.execute()]


@router.post("", response_model=BatchResponse, status_code=http_status.HTTP_201_CREATED)
def create_batch(
    body: BatchCreate,
    usecase: Annotated[CreateBatchUseCase, Depends(get_create_batch_usecase)],
) -> BatchResponse:
    batch = BatchEntity(
        name=body.name, purchase_date=body.purchase_date, notes=body.notes
    )
    return BatchResponse.from_entity(usecase.execute(batch))


@router.delete("/{batch_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_batch(
    batch_id: UUID,
    usecase: Annotated[DeleteBatchUseCase, Depends(get_delete_batch_usecase)],
) -> None:
    usecase.execute(batch_id)
