"""Contratos abstractos de servicios de infraestructura."""
from abc import ABC, abstractmethod
from typing import Any


class IEncryptionService(ABC):
    """Cifra/descifra las contraseñas de las cuentas gestionadas (Fernet)."""

    @abstractmethod
    def encrypt(self, plain: str) -> str: ...

    @abstractmethod
    def decrypt(self, token: str) -> str: ...


class IAuthService(ABC):
    """Hashing de contraseñas de usuarios del sistema y emisión/validación de JWT."""

    @abstractmethod
    def hash_password(self, plain: str) -> str: ...

    @abstractmethod
    def verify_password(self, plain: str, hashed: str) -> bool: ...

    @abstractmethod
    def create_access_token(self, subject: str, claims: dict[str, Any]) -> str: ...

    @abstractmethod
    def decode_token(self, token: str) -> dict[str, Any]: ...


class IFileParser(ABC):
    """Convierte un archivo CSV o Excel (.xlsx) en filas de diccionarios."""

    @abstractmethod
    def parse(self, content: bytes, filename: str) -> list[dict[str, str]]:
        """Devuelve las filas del archivo con encabezados normalizados (minúscula/trim)."""
        ...
