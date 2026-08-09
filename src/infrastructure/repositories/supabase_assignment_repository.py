"""Repositorio de asignaciones cuenta -> usuario sobre Supabase."""
from uuid import UUID

from supabase import Client

from ...domain.entities.assignment import AssignmentEntity
from ...domain.interfaces.repositories import IAssignmentRepository


class SupabaseAssignmentRepository(IAssignmentRepository):
    TABLE = "assignments"

    def __init__(self, client: Client) -> None:
        self._client = client

    def bulk_assign(
        self, account_ids: list[UUID], user_id: UUID, assigned_by: UUID | None
    ) -> int:
        if not account_ids:
            return 0
        rows = [
            {
                "account_id": str(account_id),
                "user_id": str(user_id),
                "assigned_by": str(assigned_by) if assigned_by else None,
            }
            for account_id in account_ids
        ]
        # upsert con ignore_duplicates: respeta el unique(account_id, user_id).
        res = (
            self._client.table(self.TABLE)
            .upsert(rows, on_conflict="account_id,user_id", ignore_duplicates=True)
            .execute()
        )
        return len(res.data)

    def list_by_user(self, user_id: UUID) -> list[AssignmentEntity]:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("user_id", str(user_id))
            .order("assigned_at", desc=True)
            .execute()
        )
        return [AssignmentEntity(**row) for row in res.data]

    def list_by_account(self, account_id: UUID) -> list[AssignmentEntity]:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("account_id", str(account_id))
            .order("assigned_at", desc=True)
            .execute()
        )
        return [AssignmentEntity(**row) for row in res.data]

    def list_assigned_account_ids(self) -> list[UUID]:
        res = self._client.table(self.TABLE).select("account_id").execute()
        return list(dict.fromkeys(UUID(row["account_id"]) for row in res.data))

    def unassign(self, account_id: UUID, user_id: UUID) -> None:
        (
            self._client.table(self.TABLE)
            .delete()
            .eq("account_id", str(account_id))
            .eq("user_id", str(user_id))
            .execute()
        )
