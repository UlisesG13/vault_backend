"""Configuración centralizada leída desde variables de entorno (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Supabase
    supabase_url: str
    supabase_key: str

    # Cifrado de contraseñas de cuentas (Fernet)
    fernet_key: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS: lista de orígenes permitidos separados por coma. "*" = cualquiera (solo dev).
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración (cacheada) para inyectarla con Depends."""
    return Settings()  # type: ignore[call-arg]
