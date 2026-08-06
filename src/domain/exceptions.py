"""Excepciones de dominio, independientes de FastAPI/HTTP.

La capa API las traduce a HTTPException en un handler global (ver src/main.py).
"""


class DomainError(Exception):
    """Base de todos los errores de negocio."""


class NotFoundError(DomainError):
    """La entidad solicitada no existe."""


class DuplicateEmailError(DomainError):
    """Ya existe una cuenta con ese correo."""


class InvalidCredentialsError(DomainError):
    """Email o contraseña incorrectos en el login."""


class AuthenticationError(DomainError):
    """Token ausente, inválido o expirado."""


class AuthorizationError(DomainError):
    """El usuario autenticado no tiene permiso para esta acción."""
