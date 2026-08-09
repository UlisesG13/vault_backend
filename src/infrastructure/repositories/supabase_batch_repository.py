"""Repositorio de lotes de cuentas sobre Supabase."""
from datetime import date
from typing import Any
from uuid import UUID

from supabase import Client

from ...domain.entities.batch import BatchEntity
from ...domain.interfaces.repositories import IBatchRepository


def _jsonify(value: Any) -> Any:
    return value.isoformat() if isinstance(value, date) else value


class SupabaseBatchRepository(IBatchRepository):
    TABLE = "account_batches"

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(self) -> list[BatchEntity]:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return [BatchEntity(**row) for row in res.data]

    def get(self, batch_id: UUID) -> BatchEntity | None:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("id", str(batch_id))
            .limit(1)
            .execute()
        )
        return BatchEntity(**res.data[0]) if res.data else None

    def create(self, batch: BatchEntity) -> BatchEntity:
        row = {
            "name": batch.name,
            "purchase_date": _jsonify(batch.purchase_date),
            "notes": batch.notes,
        }
        res = self._client.table(self.TABLE).insert(row).execute()
        return BatchEntity(**res.data[0])

    def delete(self, batch_id: UUID) -> None:
        self._client.table(self.TABLE).delete().eq("id", str(batch_id)).execute()
