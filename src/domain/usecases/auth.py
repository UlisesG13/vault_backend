"""Caso de uso: autenticación de usuarios del sistema."""
from ..exceptions import InvalidCredentialsError
from ..interfaces.repositories import IUserRepository
from ..interfaces.services import IAuthService


class LoginUseCase:
    def __init__(self, users: IUserRepository, auth: IAuthService) -> None:
        self._users = users
        self._auth = auth

    def execute(self, email: str, password: str) -> str:
        user = self._users.get_by_email(email)
        if user is None or not self._auth.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Email o contraseña incorrectos")

        return self._auth.create_access_token(
            subject=str(user.id),
            claims={"email": user.email, "role": user.role.value},
        )
