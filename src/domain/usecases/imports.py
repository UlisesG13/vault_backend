"""Importación inteligente: crea cuentas desde un CSV/Excel asociando servidor,
lote y (opcionalmente) un operador, en un solo paso."""
from typing import Any
from uuid import UUID

from pydantic import ValidationError as PydanticValidationError

from ..entities.account import AccountEntity, ProfileEntity
from ..entities.enums import UserRole
from ..exceptions import NotFoundError, ValidationError
from ..interfaces.repositories import (
    IAccountRepository,
    IAssignmentRepository,
    IAuditRepository,
    IBatchRepository,
    IServerRepository,
    IUserRepository,
)
from ..interfaces.services import IEncryptionService, IFileParser

# Máximo de filas por importación (evita cargas abusivas).
MAX_ROWS = 1000

# Alias de encabezados (español -> campo canónico). Las claves llegan normalizadas.
_ALIASES = {
    "plataforma": "platform",
    "correo": "email",
    "contraseña": "password",
    "contrasena": "password",
    "clave": "password",
    "correo_recuperacion": "recovery_email",
    "recuperacion": "recovery_email",
    "nombre": "full_name",
    "nombre_completo": "full_name",
    "telefono": "phone",
    "fecha_nacimiento": "birth_date",
    "usuario_x": "x_username",
    "usuario_fb": "fb_username",
}

_EMPTY = {"", "-", "n/a", "na", "null", "none"}


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    return None if v.lower() in _EMPTY else v


def _canon(row: dict[str, str]) -> dict[str, str | None]:
    """Aplica alias y limpia valores vacíos."""
    out: dict[str, str | None] = {}
    for key, value in row.items():
        canon = _ALIASES.get(key, key)
        out[canon] = _clean(value)
    return out


class ImportAccountsUseCase:
    def __init__(
        self,
        accounts: IAccountRepository,
        encryption: IEncryptionService,
        assignments: IAssignmentRepository,
        audit: IAuditRepository,
        parser: IFileParser,
        servers: IServerRepository,
        batches: IBatchRepository,
        users: IUserRepository,
    ) -> None:
        self._accounts = accounts
        self._encryption = encryption
        self._assignments = assignments
        self._audit = audit
        self._parser = parser
        self._servers = servers
        self._batches = batches
        self._users = users

    def execute(
        self,
        content: bytes,
        filename: str,
        server_id: UUID,
        batch_id: UUID,
        operator_id: UUID | None,
        actor_id: UUID | None,
    ) -> dict[str, Any]:
        # 1) Validar relaciones destino.
        if self._servers.get(server_id) is None:
            raise NotFoundError(f"No existe el servidor {server_id}")
        if self._batches.get(batch_id) is None:
            raise NotFoundError(f"No existe el lote {batch_id}")
        if operator_id is not None:
            operator = self._users.get_by_id(operator_id)
            if operator is None:
                raise NotFoundError(f"No existe el usuario {operator_id}")
            if operator.role == UserRole.admin:
                raise ValidationError("No se pueden asignar cuentas a un administrador")

        # 2) Parsear archivo.
        rows = self._parser.parse(content, filename)
        if not rows:
            raise ValidationError("El archivo no contiene filas")
        if len(rows) > MAX_ROWS:
            raise ValidationError(f"El archivo excede el máximo de {MAX_ROWS} filas")

        # 3) Construir entidades validando fila a fila (best-effort).
        to_insert: list[tuple[AccountEntity, ProfileEntity]] = []
        skipped_emails: list[str] = []
        row_errors: list[dict[str, Any]] = []
        seen: set[str] = set()

        for index, raw in enumerate(rows, start=2):  # fila 1 = encabezados
            data = _canon(raw)
            email = (data.get("email") or "").lower()
            password = data.get("password")

            try:
                if not email:
                    raise ValueError("falta el correo")
                if not password:
                    raise ValueError("falta la contraseña")
                account = AccountEntity(
                    platform=data.get("platform"),  # type: ignore[arg-type]
                    email=email,
                    encrypted_password="",  # se rellena tras cifrar
                    recovery_email=data.get("recovery_email"),
                    server_id=server_id,
                    batch_id=batch_id,
                )
                profile = ProfileEntity(
                    full_name=data.get("full_name"),
                    phone=data.get("phone"),
                    birth_date=data.get("birth_date"),  # type: ignore[arg-type]
                    x_username=data.get("x_username"),
                    fb_username=data.get("fb_username"),
                )
            except (PydanticValidationError, ValueError) as exc:
                row_errors.append({"row": index, "reason": str(exc)})
                continue

            if email in seen or self._accounts.get_by_email(email) is not None:
                skipped_emails.append(email)
                continue
            seen.add(email)
            account.encrypted_password = self._encryption.encrypt(password)
            to_insert.append((account, profile))

        # 4) Insertar en lote y asignar.
        created_ids = self._accounts.bulk_create(to_insert) if to_insert else []
        assigned = 0
        if operator_id is not None and created_ids:
            assigned = self._assignments.bulk_assign(created_ids, operator_id, actor_id)

        self._audit.log(
            action="imported",
            system_user_id=actor_id,
            details={
                "server_id": str(server_id),
                "batch_id": str(batch_id),
                "operator_id": str(operator_id) if operator_id else None,
                "inserted": len(created_ids),
                "skipped": len(skipped_emails),
                "errors": len(row_errors),
                "assigned": assigned,
            },
        )
        return {
            "inserted": len(created_ids),
            "skipped": len(skipped_emails),
            "assigned": assigned,
            "skipped_emails": skipped_emails,
            "row_errors": row_errors,
        }
