Contexto: Necesito una API RESTful para gestionar un repositorio de cuentas digitales (credenciales). La base de datos será Supabase (PostgreSQL). El sistema debe tener autenticación por JWT.

Tecnologías obligatorias:

Python 3.11+.

FastAPI como framework web.

Pydantic v2 para la validación de datos y serialización.

Supabase Python SDK (supabase-py) para la interacción con la base de datos.

python-dotenv para variables de entorno.

Passlib o bcrypt para hashear contraseñas de usuario del sistema (no confundir con las contraseñas de las cuentas gestionadas, que deben cifrarse).

PyJWT o python-jose para la creación/verificación de tokens JWT.

Cryptography (Fernet) para cifrar/descifrar las contraseñas de las cuentas (Gmail/Facebook) antes de guardarlas en Supabase.

Arquitectura obligatoria (Clean Architecture / Hexagonal):
Debes organizar el código en capas claramente separadas para facilitar el mantenimiento y las pruebas:

src/domain/entities/: Modelos de negocio puros (definidos con Pydantic, pero sin lógica de base de datos). Ej: AccountEntity, UserEntity.

src/domain/usecases/: Casos de uso específicos (ej: CreateAccountUseCase, UpdateStatusUseCase, GetAccountsUseCase). Aquí va la lógica de negocio (ej: "no se pueden guardar dos cuentas con el mismo correo").

src/domain/interfaces/: Definición de contratos abstractos (ej: IAccountRepository, IAuthService). Esto permite desacoplar la lógica de la infraestructura.

src/infrastructure/repositories/: Implementación concreta de los repositorios usando el cliente de Supabase. Ej: SupabaseAccountRepository.

src/infrastructure/services/: Servicios externos (ej: JWTService, EncryptionService para cifrar contraseñas con Fernet).

src/api/routers/: Endpoints de FastAPI (ej: auth_router.py, accounts_router.py).

src/api/schemas/: DTOs (Data Transfer Objects) específicos para la API (Request y Response models).

src/core/config.py: Configuración centralizada (Supabase URL, Supabase Key, Fernet Key, JWT Secret).

Base de Datos (Supabase - Esquema):
Dentro de Supabase, crea las siguientes tablas (puedes usar el Editor SQL de Supabase):

sql
-- Tabla de usuarios del sistema (quienes usan el panel)
CREATE TABLE system_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT DEFAULT 'gestor', -- 'admin', 'gestor', 'lector'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla principal de cuentas gestionadas
CREATE TABLE managed_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL, -- 'gmail', 'facebook', 'twitter'
    email TEXT NOT NULL UNIQUE,
    encrypted_password TEXT NOT NULL, -- Cifrado con Fernet
    recovery_email TEXT,
    status TEXT DEFAULT 'active', -- 'active', 'suspended', 'verification_needed'
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de datos personales (1 a 1 con managed_accounts)
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES managed_accounts(id) ON DELETE CASCADE,
    full_name TEXT,
    phone TEXT,
    birth_date DATE,
    x_username TEXT,
    fb_username TEXT
);

-- Tabla de auditoría
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    account_id UUID REFERENCES managed_accounts(id) ON DELETE SET NULL,
    system_user_id UUID REFERENCES system_users(id) ON DELETE SET NULL,
    action TEXT NOT NULL, -- 'viewed', 'updated_status', 'edited_password', 'deleted'
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
Endpoint Endpoints obligatorios (API REST):

POST /api/auth/login: Recibe email y password, valida contra system_users, retorna JWT.

GET /api/accounts: Lista todas las cuentas con filtros (status, platform, search), paginación (skip/limit) y ordenación. Al listar, NO envíes el campo encrypted_password por seguridad (solo envía el resto).

GET /api/accounts/{id}: Obtiene una cuenta específica (solo para este endpoint, descifra la contraseña y envíala en el campo password para mostrarla en el frontend).

PATCH /api/accounts/{id}/status: Actualiza solo el estado de la cuenta.

PUT /api/accounts/{id}: Actualiza todos los campos (nombre, teléfono, contraseña, etc.). Si se envía una nueva contraseña, debe cifrarla antes de guardar.

POST /api/accounts/bulk: Recibe un array de cuentas en el body y las inserta masivamente (ignora duplicados basados en email con ON CONFLICT DO NOTHING o manejándolo en código).

DELETE /api/accounts/{id}: Elimina la cuenta y su perfil en cascada (auditar esta acción).

Buenas prácticas de programación exigidas:

Inyección de Dependencias: Usa Depends de FastAPI para inyectar los repositorios y servicios en los routers.

Manejo de errores global: Implementa un middleware o handler global para capturar excepciones y devolver errores formateados con HTTPException.

Variables de entorno: Todas las claves (Supabase, Fernet, JWT) deben leerse desde .env.

Cifrado seguro: Usa la librería cryptography.fernet con una clave generada de 32 bytes (base64). Guarda la clave en las variables de entorno.

Asincronía vs Sincronía: El SDK de Supabase es principalmente síncrono. Usa fastapi.concurrency.run_in_threadpool si quieres mantener los endpoints asíncronos, o simplemente define las funciones de los routers como def síncronas. Prioriza la legibilidad.

Logging: Implementa logs básicos para peticiones críticas.

