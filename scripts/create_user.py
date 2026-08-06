"""Crea un usuario del sistema (para poder hacer login).

Uso:
    python -m scripts.create_user <email> <password> [role]

role: admin | operator  (por defecto: admin)
"""
import sys

from src.core.config import get_settings
from src.infrastructure.services.auth_service import AuthService
from src.infrastructure.services.supabase_client import get_supabase_client


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    email = sys.argv[1].lower()
    password = sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else "admin"

    settings = get_settings()
    auth = AuthService(settings.jwt_secret, settings.jwt_algorithm, settings.access_token_expire_minutes)
    client = get_supabase_client()

    row = {"email": email, "hashed_password": auth.hash_password(password), "role": role}
    client.table("system_users").insert(row).execute()
    print(f"Usuario creado: {email} (role={role})")


if __name__ == "__main__":
    main()
