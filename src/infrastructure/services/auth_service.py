"""Hashing de contraseñas (bcrypt) y emisión/validación de JWT (python-jose)."""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from ...domain.exceptions import AuthenticationError
from ...domain.interfaces.services import IAuthService


class AuthService(IAuthService):
    def __init__(self, secret: str, algorithm: str, expire_minutes: int) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    @staticmethod
    def _to_bytes(plain: str) -> bytes:
        # bcrypt solo considera los primeros 72 bytes; truncamos para evitar errores.
        return plain.encode("utf-8")[:72]

    def hash_password(self, plain: str) -> str:
        return bcrypt.hashpw(self._to_bytes(plain), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(self._to_bytes(plain), hashed.encode("utf-8"))

    def create_access_token(self, subject: str, claims: dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._expire_minutes)).timestamp()),
            **claims,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except ExpiredSignatureError as exc:
            raise AuthenticationError("El token ha expirado") from exc
        except JWTError as exc:
            raise AuthenticationError("Token inválido") from exc
