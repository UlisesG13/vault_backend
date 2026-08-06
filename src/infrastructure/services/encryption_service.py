"""Cifrado simétrico de las contraseñas de las cuentas gestionadas (Fernet)."""
from cryptography.fernet import Fernet

from ...domain.interfaces.services import IEncryptionService


class FernetEncryptionService(IEncryptionService):
    def __init__(self, fernet_key: str) -> None:
        # La clave debe ser 32 bytes url-safe base64 (Fernet.generate_key()).
        self._fernet = Fernet(fernet_key.encode())

    def encrypt(self, plain: str) -> str:
        return self._fernet.encrypt(plain.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self._fernet.decrypt(token.encode()).decode()
