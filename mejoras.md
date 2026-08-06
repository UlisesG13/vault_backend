Contexto:
Backend para gestión de cuentas digitales. Usamos FastAPI y la conexión a Supabase se hace mediante MCP (Model Context Protocol), por lo que puedes interactuar directamente con las tablas de Supabase usando el cliente de Python (supabase-py) o directamente las funciones del MCP.
La base de datos ya debe tener las siguientes tablas (proporciona este esquema exacto al agente):

sql
-- Usuarios del sistema (Admin y Operadores)
CREATE TABLE system_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'operator')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cuentas gestionadas (Gmail, FB, X)
CREATE TABLE managed_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL CHECK (platform IN ('gmail', 'facebook', 'twitter')),
    email TEXT NOT NULL UNIQUE,
    encrypted_password TEXT NOT NULL, -- Cifrado con Fernet
    recovery_email TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'banned')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Perfiles (datos personales asociados)
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES managed_accounts(id) ON DELETE CASCADE,
    full_name TEXT,
    phone TEXT,
    birth_date DATE,
    x_username TEXT,
    fb_username TEXT
);

-- Auditoría (logs de acciones)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    account_id UUID REFERENCES managed_accounts(id) ON DELETE SET NULL,
    system_user_id UUID REFERENCES system_users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
Arquitectura (Clean Architecture en capas):

src/domain/entities/: Modelos Pydantic (UserEntity, AccountEntity, ProfileEntity).

src/domain/usecases/: Lógica de negocio (ej: create_account, get_admin_stats, create_operator). Aquí se aplican reglas como "no duplicar emails" o "cifrar contraseña antes de guardar".

src/infrastructure/supabase/: Cliente de Supabase (configurado con URL y KEY desde .env) y funciones directas CRUD.

src/api/routers/: Endpoints de FastAPI (auth, accounts, admin).

src/api/dependencies.py: Dependencias para validar JWT y roles.

Endpoint Endpoints y reglas de negocio:

Auth:

POST /api/auth/login: Recibe email/password, verifica contra system_users (usa bcrypt para comparar), devuelve JWT con { id, email, role }.

Accounts (Ambos roles):

GET /api/accounts: Lista paginada con filtros (status, platform, search). Aquí ambos roles (admin y operator) pueden ver las contraseñas, así que en la respuesta JSON descifra el password con Fernet y envíalo en el campo password (no lo ocultes en el backend, el frontend lo ocultará visualmente).

GET /api/accounts/{id}: Obtiene detalle completo con el password descifrado.

POST /api/accounts: Crea cuenta. Cifra password con Fernet antes de insertar. Inserta también en profiles si vienen datos.

PUT /api/accounts/{id}: Actualiza. Si llega un nuevo password, lo cifra.

PATCH /api/accounts/{id}/status: Cambia el estado.

DELETE /api/accounts/{id}: Elimina en cascada (account + profile). Registra en audit_logs.

POST /api/accounts/bulk: Recibe array de cuentas y las inserta en lote (ignora duplicados por email).

Admin (SOLO rol 'admin'):

GET /api/admin/stats: Devuelve estadísticas:
{ total, active, suspended, banned, created_today, platform_distribution: {gmail: x, facebook: y, twitter: z}, trend_last_7_days: [{date, created, deleted}] }.

GET /api/admin/users: Lista todos los system_users con role = 'operator'.

POST /api/admin/users: Crea un operador. Recibe { email, password }. Hashea la password con bcrypt y guarda con role='operator'.

DELETE /api/admin/users/{id}: Elimina un operador (solo si no es admin).

Seguridad:

Usa python-jose para JWT.

Usa cryptography.fernet para cifrar contraseñas de cuentas (la clave maestra en .env).

Dependencia require_role(["admin"]) para rutas de admin.

Dependencia require_role(["admin", "operator"]) para rutas de cuentas.

No existe endpoint de registro público. Solo el admin puede crear operadores.

Estructura de variables de entorno (.env):

text
SUPABASE_URL=...
SUPABASE_KEY=...
FERNET_KEY=... (clave de 32 bytes en base64)
JWT_SECRET=...