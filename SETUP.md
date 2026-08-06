# Vault Backend — Guía de arranque

API REST (FastAPI) para gestionar credenciales de cuentas digitales, con
Supabase (PostgreSQL) como base de datos, JWT para autenticación y Fernet para
cifrar las contraseñas de las cuentas gestionadas.

## Arquitectura (Clean / Hexagonal)

```
src/
├─ core/config.py              # Configuración desde .env (pydantic-settings)
├─ domain/                     # Núcleo, sin dependencias de framework/DB
│  ├─ entities/                # Modelos de negocio (AccountEntity, UserEntity, enums)
│  ├─ usecases/                # Lógica de negocio (auth, accounts)
│  ├─ interfaces/              # Puertos: IAccountRepository, IAuthService, ...
│  └─ exceptions.py            # Errores de dominio (mapeados a HTTP en main.py)
├─ infrastructure/             # Adaptadores concretos
│  ├─ repositories/            # Implementaciones con supabase-py
│  └─ services/                # Fernet, JWT/bcrypt, cliente Supabase
└─ api/                        # Capa web (FastAPI)
   ├─ routers/                 # auth_router, accounts_router
   ├─ schemas/                 # DTOs Request/Response
   └─ dependencies.py          # Inyección de dependencias (Depends)
```

El flujo es: **router → caso de uso → repositorio/servicio (vía interfaz)**. El
dominio no conoce FastAPI ni Supabase; se inyectan por `Depends` en
`api/dependencies.py`.

## 1. Requisitos

- Python 3.11+
- Un proyecto en [Supabase](https://supabase.com)

## 2. Instalación

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt
```

## 3. Base de datos

En el **SQL Editor** de Supabase, ejecuta el contenido de [`sql/schema.sql`](sql/schema.sql).

## 4. Variables de entorno

```bash
cp .env.example .env
```

Genera las claves y complétalas en `.env`:

```bash
# Clave Fernet (cifrado de contraseñas de cuentas)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Secreto JWT
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`SUPABASE_URL` y `SUPABASE_KEY` están en Supabase → Project Settings → API.

> 🔒 **`SUPABASE_KEY` DEBE ser la clave `service_role`** (sección "service_role
> secret"). La base de datos tiene RLS activo y **bloquea** las claves
> `anon`/`publishable`, así que solo `service_role` (que ignora RLS) puede operar.
> Es una clave secreta: mantenla solo en el servidor y nunca la subas a git.

> ⚠️ La `FERNET_KEY` no debe cambiar una vez que haya contraseñas cifradas en la
> DB: si la pierdes o la rotas, no podrás descifrar lo ya guardado.

## 5. Crear el primer usuario del sistema

Login valida contra `system_users`, así que crea uno:

```bash
python -m scripts.create_user admin@ejemplo.com "MiPasswordSegura" admin
```

## 6. Ejecutar

```bash
uvicorn src.main:app --reload
```

- Docs interactivas: http://127.0.0.1:8000/docs
- Healthcheck: http://127.0.0.1:8000/health

## 7. Roles y endpoints

Dos roles: **`admin`** y **`operator`**. Las rutas de `/api/accounts` requieren
`admin` **o** `operator`; las de `/api/admin` requieren **`admin`**. No hay
registro público: solo un admin crea operadores.

### Cuentas — `admin` y `operator`

| Método | Ruta                             | Descripción                                    |
|--------|----------------------------------|------------------------------------------------|
| POST   | `/api/auth/login`                | Devuelve un JWT `{ id, email, role }`          |
| GET    | `/api/accounts`                  | Lista (filtros: `status`, `platform`, `search`; `skip`/`limit`) — **con** contraseña descifrada |
| GET    | `/api/accounts/{id}`             | Detalle **con** la contraseña descifrada       |
| POST   | `/api/accounts`                  | Crea una cuenta (cifra la contraseña)          |
| PUT    | `/api/accounts/{id}`             | Actualiza todos los campos (re-cifra si hay nueva contraseña) |
| PATCH  | `/api/accounts/{id}/status`      | Actualiza solo el `status` (`active`/`suspended`/`banned`) |
| POST   | `/api/accounts/bulk`             | Alta masiva (ignora correos duplicados)        |
| DELETE | `/api/accounts/{id}`             | Elimina la cuenta (perfil en cascada), auditado |

### Admin — solo `admin`

| Método | Ruta                        | Descripción                                         |
|--------|-----------------------------|-----------------------------------------------------|
| GET    | `/api/admin/stats`          | Totales, `created_today`, `platform_distribution`, `trend_last_7_days` |
| GET    | `/api/admin/users`          | Lista los usuarios con rol `operator`               |
| POST   | `/api/admin/users`          | Crea un operador `{ email, password }` (hash bcrypt)|
| DELETE | `/api/admin/users/{id}`     | Elimina un operador (rechaza si el objetivo es admin)|

Todos los endpoints (excepto `/api/auth/login`) requieren el header
`Authorization: Bearer <token>`.

### Ejemplo rápido

```bash
# 1) Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ejemplo.com","password":"MiPasswordSegura"}' | jq -r .access_token)

# 2) Crear cuenta
curl -X POST http://127.0.0.1:8000/api/accounts \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"platform":"gmail","email":"cuenta@gmail.com","password":"secreto123","full_name":"Juan Pérez"}'

# 3) Listar
curl -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8000/api/accounts?platform=gmail"
```

## Notas de seguridad

- **Base de datos blindada:** RLS activo en las 4 tablas (sin policies) y todos
  los privilegios revocados a `anon`/`authenticated`. Las claves públicas no
  pueden leer ni escribir nada; solo la `service_role` del backend opera.
- **CORS** restringido a `CORS_ORIGINS` (.env); la API usa Bearer tokens, sin cookies.
- Las **contraseñas de cuentas gestionadas** se cifran con Fernet. Se descifran
  y se envían en el campo `password` tanto en el listado como en el detalle
  (ambos roles las ven; el frontend las oculta visualmente).
- Las **contraseñas de usuarios del sistema** se hashean con bcrypt (irreversible).
- Autorización por rol vía `require_role(...)`: `["admin","operator"]` en cuentas,
  `["admin"]` en el panel de administración.
- Cada lectura de contraseña, cambio de estado, edición y borrado queda en
  `audit_logs`.
