"""Repositorio de usuarios del sistema sobre Supabase."""
from uuid import UUID

from supabase import Client

from ...domain.entities.user import UserEntity
from ...domain.interfaces.repositories import IUserRepository


class SupabaseUserRepository(IUserRepository):
    TABLE = "system_users"

    def __init__(self, client: Client) -> None:
        self._client = client

    def get_by_email(self, email: str) -> UserEntity | None:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("email", email.lower())
            .limit(1)
            .execute()
        )
        return UserEntity(**res.data[0]) if res.data else None

    def get_by_id(self, user_id: UUID) -> UserEntity | None:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("id", str(user_id))
            .limit(1)
            .execute()
        )
        return UserEntity(**res.data[0]) if res.data else None

    def list_by_role(self, role: str) -> list[UserEntity]:
        res = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("role", role)
            .order("created_at", desc=True)
            .execute()
        )
        return [UserEntity(**row) for row in res.data]

    def create(self, email: str, hashed_password: str, role: str) -> UserEntity:
        row = {"email": email.lower(), "hashed_password": hashed_password, "role": role}
        res = self._client.table(self.TABLE).insert(row).execute()
        return UserEntity(**res.data[0])

    def delete(self, user_id: UUID) -> None:
        self._client.table(self.TABLE).delete().eq("id", str(user_id)).execute()
