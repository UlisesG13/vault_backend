"""Estadísticas agregadas de cuentas gestionadas (para el panel de admin)."""
from collections import Counter
from datetime import date, timedelta
from typing import Any

from supabase import Client

from ...domain.interfaces.repositories import IStatsRepository

ACCOUNTS = "managed_accounts"
AUDIT = "audit_logs"
SERVERS = "servers"
_PLATFORMS = ("gmail", "facebook", "twitter")
_TREND_DAYS = 7


class SupabaseStatsRepository(IStatsRepository):
    def __init__(self, client: Client) -> None:
        self._client = client

    def _count(self, **filters: str) -> int:
        query = self._client.table(ACCOUNTS).select("id", count="exact")
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute().count or 0

    def get_stats(self) -> dict[str, Any]:
        today = date.today()
        start = today - timedelta(days=_TREND_DAYS - 1)
        start_iso = f"{start.isoformat()}T00:00:00+00:00"

        # Tendencia: altas por día (created_at) y bajas por día (audit_logs action=deleted)
        created_rows = (
            self._client.table(ACCOUNTS)
            .select("created_at")
            .gte("created_at", start_iso)
            .execute()
            .data
        )
        deleted_rows = (
            self._client.table(AUDIT)
            .select("created_at")
            .eq("action", "deleted")
            .gte("created_at", start_iso)
            .execute()
            .data
        )
        created_by_day = Counter(r["created_at"][:10] for r in created_rows)
        deleted_by_day = Counter(r["created_at"][:10] for r in deleted_rows)

        trend = []
        for offset in range(_TREND_DAYS):
            day = (start + timedelta(days=offset)).isoformat()
            trend.append(
                {
                    "date": day,
                    "created": created_by_day.get(day, 0),
                    "deleted": deleted_by_day.get(day, 0),
                }
            )

        created_today = (
            self._client.table(ACCOUNTS)
            .select("id", count="exact")
            .gte("created_at", f"{today.isoformat()}T00:00:00+00:00")
            .execute()
            .count
            or 0
        )

        return {
            "total": self._count(),
            "active": self._count(status="active"),
            "suspended": self._count(status="suspended"),
            "banned": self._count(status="banned"),
            "created_today": created_today,
            "platform_distribution": {p: self._count(platform=p) for p in _PLATFORMS},
            "trend_last_7_days": trend,
            "servers": self._server_usage(),
        }

    def _server_usage(self) -> list[dict[str, Any]]:
        """Conteo de cuentas por servidor, incluyendo servidores con 0 cuentas."""
        servers = (
            self._client.table(SERVERS)
            .select("id, name, description")
            .order("name")
            .execute()
            .data
        )
        server_ids = (
            self._client.table(ACCOUNTS).select("server_id").execute().data
        )
        # Mismo patrón que la tendencia: agrupar/contar en Python con Counter.
        counts = Counter(
            row["server_id"] for row in server_ids if row.get("server_id")
        )
        return [
            {
                "id": s["id"],
                "name": s["name"],
                "description": s.get("description"),
                "count": counts.get(s["id"], 0),
            }
            for s in servers
        ]
