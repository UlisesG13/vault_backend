"""Repositorio de auditoría sobre Supabase."""
from typing import Any
from uuid import UUID

from supabase import Client

from ...domain.interfaces.repositories import IAuditRepository


class SupabaseAuditRepository(IAuditRepository):
    TABLE = "audit_logs"
    USERS = "system_users"
    ACCOUNTS = "managed_accounts"

    def __init__(self, client: Client) -> None:
        self._client = client

    def log(
        self,
        *,
        action: str,
        account_id: UUID | None = None,
        system_user_id: UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        row = {
            "action": action,
            "account_id": str(account_id) if account_id else None,
            "system_user_id": str(system_user_id) if system_user_id else None,
            "details": details or {},
        }
        self._client.table(self.TABLE).insert(row).execute()

    def list_recent(self, limit: int) -> list[dict[str, Any]]:
        rows = (
            self._client.table(self.TABLE)
            .select("action, account_id, system_user_id, details, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
        )
        if not rows:
            return []

        user_ids = {r["system_user_id"] for r in rows if r.get("system_user_id")}
        account_ids = {r["account_id"] for r in rows if r.get("account_id")}
        emails: dict[str, str] = {}

        if user_ids:
            users = (
                self._client.table(self.USERS)
                .select("id, email")
                .in_("id", sorted(user_ids))
                .execute()
                .data
            )
            emails.update({str(u["id"]): u["email"] for u in users})

        account_emails: dict[str, str] = {}
        if account_ids:
            accounts = (
                self._client.table(self.ACCOUNTS)
                .select("id, email")
                .in_("id", sorted(account_ids))
                .execute()
                .data
            )
            account_emails.update({str(a["id"]): a["email"] for a in accounts})

        return [
            {
                "action": row["action"],
                "details": row.get("details") or {},
                "account_id": row.get("account_id"),
                "account_email": account_emails.get(row.get("account_id") or ""),
                "user_email": emails.get(row.get("system_user_id") or ""),
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]
