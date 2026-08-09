"""Casos de uso sobre lotes de cuentas (solo rol admin)."""
from uuid import UUID

from ..entities.batch import BatchEntity
from ..exceptions import NotFoundError
from ..interfaces.repositories import IBatchRepository


class ListBatchesUseCase:
    def __init__(self, batches: IBatchRepository) -> None:
        self._batches = batches

    def execute(self) -> list[BatchEntity]:
        return self._batches.list()


class GetBatchUseCase:
    def __init__(self, batches: IBatchRepository) -> None:
        self._batches = batches

    def execute(self, batch_id: UUID) -> BatchEntity:
        batch = self._batches.get(batch_id)
        if batch is None:
            raise NotFoundError(f"No existe el lote {batch_id}")
        return batch


class CreateBatchUseCase:
    def __init__(self, batches: IBatchRepository) -> None:
        self._batches = batches

    def execute(self, batch: BatchEntity) -> BatchEntity:
        return self._batches.create(batch)


class DeleteBatchUseCase:
    def __init__(self, batches: IBatchRepository) -> None:
        self._batches = batches

    def execute(self, batch_id: UUID) -> None:
        if self._batches.get(batch_id) is None:
            raise NotFoundError(f"No existe el lote {batch_id}")
        # Cuentas y gastos ligados quedan con batch_id = NULL (ON DELETE SET NULL).
        self._batches.delete(batch_id)
