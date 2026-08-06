"""Repositorio de cuentas gestionadas sobre Supabase.

`managed_accounts` (1) --- (1) `profiles`. Se leen juntas con el embedding de
PostgREST: select("*, profiles(*)").
"""
from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from supabase import Client

from ...domain.entities.account import AccountEntity, ProfileEntity
from ...domain.entities.enums import AccountStatus
from ...domain.interfaces.repositories import IAccountRepository

ACCOUNTS = "managed_accounts"
PROFILES = "profiles"
_SELECT = "*, profiles(*)"


def _jsonify(value: Any) -> Any:
    return value.isoformat() if isinstance(value, date) else value


def _row_to_entity(row: dict[str, Any]) -> AccountEntity:
    embedded = row.get("profiles")
    # El embedding llega como lista (lado "muchos"); tomamos el primero.
    if isinstance(embedded, list):
        profile_data = embedded[0] if embedded else None
    else:
        profile_data = embedded

    profile = ProfileEntity(**profile_data) if profile_data else None
    return AccountEntity(
        id=row["id"],
        platform=row["platform"],
        email=row["email"],
        encrypted_password=row["encrypted_password"],
        recovery_email=row.get("recovery_email"),
        status=row["status"],
        notes=row.get("notes"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        profile=profile,
    )


class SupabaseAccountRepository(IAccountRepository):
    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        status: str | None = None,
        platform: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> list[AccountEntity]:
        query = self._client.table(ACCOUNTS).select(_SELECT)
        if status:
            query = query.eq("status", status)
        if platform:
            query = query.eq("platform", platform)
        if search:
            query = query.ilike("email", f"%{search}%")
        query = query.order(order_by, desc=descending).range(skip, skip + limit - 1)
        res = query.execute()
        return [_row_to_entity(r) for r in res.data]

    def get(self, account_id: UUID) -> AccountEntity | None:
        res = (
            self._client.table(ACCOUNTS)
            .select(_SELECT)
            .eq("id", str(account_id))
            .limit(1)
            .execute()
        )
        return _row_to_entity(res.data[0]) if res.data else None

    def get_by_email(self, email: str) -> AccountEntity | None:
        res = (
            self._client.table(ACCOUNTS)
            .select(_SELECT)
            .eq("email", email.lower())
            .limit(1)
            .execute()
        )
        return _row_to_entity(res.data[0]) if res.data else None

    def create(self, account: AccountEntity, profile: ProfileEntity) -> AccountEntity:
        account_row = {
            "platform": account.platform.value,
            "email": account.email.lower(),
            "encrypted_password": account.encrypted_password,
            "recovery_email": account.recovery_email,
            "status": account.status.value,
            "notes": account.notes,
        }
        res = self._client.table(ACCOUNTS).insert(account_row).execute()
        new_id = res.data[0]["id"]

        self._client.table(PROFILES).insert(self._profile_row(new_id, profile)).execute()
        created = self.get(UUID(new_id))
        assert created is not None
        return created

    def update(
        self,
        account_id: UUID,
        account_fields: dict[str, Any],
        profile_fields: dict[str, Any],
    ) -> AccountEntity:
        aid = str(account_id)
        if account_fields:
            payload = {k: _jsonify(v) for k, v in account_fields.items()}
            self._client.table(ACCOUNTS).update(payload).eq("id", aid).execute()

        if profile_fields:
            payload = {k: _jsonify(v) for k, v in profile_fields.items()}
            existing = (
                self._client.table(PROFILES)
                .select("id")
                .eq("account_id", aid)
                .limit(1)
                .execute()
            )
            if existing.data:
                self._client.table(PROFILES).update(payload).eq("account_id", aid).execute()
            else:
                self._client.table(PROFILES).insert({**payload, "account_id": aid}).execute()

        updated = self.get(account_id)
        assert updated is not None
        return updated

    def update_status(self, account_id: UUID, status: AccountStatus) -> AccountEntity:
        self._client.table(ACCOUNTS).update({"status": status.value}).eq(
            "id", str(account_id)
        ).execute()
        updated = self.get(account_id)
        assert updated is not None
        return updated

    def bulk_create(self, accounts: list[tuple[AccountEntity, ProfileEntity]]) -> int:
        if not accounts:
            return 0

        account_rows = [
            {
                "platform": a.platform.value,
                "email": a.email.lower(),
                "encrypted_password": a.encrypted_password,
                "recovery_email": a.recovery_email,
                "status": a.status.value,
                "notes": a.notes,
            }
            for a, _ in accounts
        ]
        res = self._client.table(ACCOUNTS).insert(account_rows).execute()

        # Mapear email -> id para asociar los perfiles correctamente.
        id_by_email = {row["email"]: row["id"] for row in res.data}
        profile_rows = [
            self._profile_row(id_by_email[a.email.lower()], p)
            for a, p in accounts
            if a.email.lower() in id_by_email
        ]
        if profile_rows:
            self._client.table(PROFILES).insert(profile_rows).execute()
        return len(res.data)

    def delete(self, account_id: UUID) -> None:
        # profiles se borra en cascada por la FK (ON DELETE CASCADE).
        self._client.table(ACCOUNTS).delete().eq("id", str(account_id)).execute()

    @staticmethod
    def _profile_row(account_id: str, profile: ProfileEntity) -> dict[str, Any]:
        return {
            "account_id": account_id,
            "full_name": profile.full_name,
            "phone": profile.phone,
            "birth_date": _jsonify(profile.birth_date),
            "x_username": profile.x_username,
            "fb_username": profile.fb_username,
        }
