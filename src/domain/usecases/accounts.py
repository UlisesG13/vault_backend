"""Casos de uso sobre cuentas gestionadas. Aquí vive la lógica de negocio."""
from typing import Any
from uuid import UUID

from ..entities.account import AccountEntity, ProfileEntity
from ..entities.enums import AccountStatus
from ..exceptions import DuplicateEmailError, NotFoundError
from ..interfaces.repositories import IAccountRepository, IAuditRepository
from ..interfaces.services import IEncryptionService


class GetAccountsUseCase:
    """Lista cuentas con filtros/paginación. No expone la contraseña."""

    def __init__(self, accounts: IAccountRepository) -> None:
        self._accounts = accounts

    def execute(self, **filters: Any) -> list[AccountEntity]:
        return self._accounts.list(**filters)


class GetAccountUseCase:
    """Obtiene una cuenta y audita el acceso. El descifrado se hace en la capa API."""

    def __init__(self, accounts: IAccountRepository, audit: IAuditRepository) -> None:
        self._accounts = accounts
        self._audit = audit

    def execute(self, account_id: UUID, actor_id: UUID | None) -> AccountEntity:
        account = self._accounts.get(account_id)
        if account is None:
            raise NotFoundError(f"No existe la cuenta {account_id}")

        self._audit.log(action="viewed", account_id=account_id, system_user_id=actor_id)
        return account


class CreateAccountUseCase:
    def __init__(
        self,
        accounts: IAccountRepository,
        encryption: IEncryptionService,
        audit: IAuditRepository,
    ) -> None:
        self._accounts = accounts
        self._encryption = encryption
        self._audit = audit

    def execute(
        self, account: AccountEntity, profile: ProfileEntity, plain_password: str,
        actor_id: UUID | None,
    ) -> AccountEntity:
        # Regla de negocio: no se permiten dos cuentas con el mismo correo.
        if self._accounts.get_by_email(account.email) is not None:
            raise DuplicateEmailError(f"Ya existe una cuenta con el correo {account.email}")

        account.encrypted_password = self._encryption.encrypt(plain_password)
        created = self._accounts.create(account, profile)
        self._audit.log(action="created", account_id=created.id, system_user_id=actor_id)
        return created


class UpdateAccountUseCase:
    """Actualiza campos de cuenta y perfil. Cifra la contraseña si viene una nueva."""

    def __init__(
        self,
        accounts: IAccountRepository,
        encryption: IEncryptionService,
        audit: IAuditRepository,
    ) -> None:
        self._accounts = accounts
        self._encryption = encryption
        self._audit = audit

    def execute(
        self,
        account_id: UUID,
        account_fields: dict[str, Any],
        profile_fields: dict[str, Any],
        new_password: str | None,
        actor_id: UUID | None,
    ) -> AccountEntity:
        if self._accounts.get(account_id) is None:
            raise NotFoundError(f"No existe la cuenta {account_id}")

        password_changed = False
        if new_password:
            account_fields["encrypted_password"] = self._encryption.encrypt(new_password)
            password_changed = True

        updated = self._accounts.update(account_id, account_fields, profile_fields)
        action = "edited_password" if password_changed else "updated"
        self._audit.log(action=action, account_id=account_id, system_user_id=actor_id)
        return updated


class UpdateStatusUseCase:
    def __init__(self, accounts: IAccountRepository, audit: IAuditRepository) -> None:
        self._accounts = accounts
        self._audit = audit

    def execute(
        self, account_id: UUID, status: AccountStatus, actor_id: UUID | None
    ) -> AccountEntity:
        if self._accounts.get(account_id) is None:
            raise NotFoundError(f"No existe la cuenta {account_id}")

        updated = self._accounts.update_status(account_id, status)
        self._audit.log(
            action="updated_status",
            account_id=account_id,
            system_user_id=actor_id,
            details={"status": status.value},
        )
        return updated


class BulkCreateAccountsUseCase:
    """Inserta cuentas en lote, ignorando las que dupliquen un correo existente."""

    def __init__(
        self,
        accounts: IAccountRepository,
        encryption: IEncryptionService,
        audit: IAuditRepository,
    ) -> None:
        self._accounts = accounts
        self._encryption = encryption
        self._audit = audit

    def execute(
        self,
        items: list[tuple[AccountEntity, ProfileEntity, str]],
        actor_id: UUID | None,
    ) -> dict[str, Any]:
        to_insert: list[tuple[AccountEntity, ProfileEntity]] = []
        skipped: list[str] = []
        seen: set[str] = set()

        for account, profile, plain_password in items:
            email = account.email.lower()
            if email in seen or self._accounts.get_by_email(email) is not None:
                skipped.append(email)
                continue
            seen.add(email)
            account.encrypted_password = self._encryption.encrypt(plain_password)
            to_insert.append((account, profile))

        created_ids = self._accounts.bulk_create(to_insert) if to_insert else []
        inserted = len(created_ids)
        self._audit.log(
            action="created",
            system_user_id=actor_id,
            details={"bulk": True, "inserted": inserted, "skipped": len(skipped)},
        )
        return {"inserted": inserted, "skipped": len(skipped), "skipped_emails": skipped}


class DeleteAccountUseCase:
    def __init__(self, accounts: IAccountRepository, audit: IAuditRepository) -> None:
        self._accounts = accounts
        self._audit = audit

    def execute(self, account_id: UUID, actor_id: UUID | None) -> None:
        if self._accounts.get(account_id) is None:
            raise NotFoundError(f"No existe la cuenta {account_id}")
        # Auditar ANTES de borrar para conservar el account_id en el log.
        self._audit.log(action="deleted", account_id=account_id, system_user_id=actor_id)
        self._accounts.delete(account_id)
