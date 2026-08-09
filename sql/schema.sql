-- Esquema de la base de datos (ejecutar en el Editor SQL de Supabase).
-- El control de acceso lo hace la API (FastAPI + JWT + require_role), no RLS.

-- Usuarios del sistema (Admin y Operadores)
create table if not exists system_users (
    id              uuid primary key default gen_random_uuid(),
    email           text unique not null,
    hashed_password text not null,
    role            text not null check (role in ('admin', 'operator')),
    created_at      timestamptz not null default now()
);

-- Cuentas gestionadas (Gmail, Facebook, X)
create table if not exists managed_accounts (
    id                 uuid primary key default gen_random_uuid(),
    platform           text not null check (platform in ('gmail', 'facebook', 'twitter')),
    email              text not null unique,
    encrypted_password text not null,               -- cifrado con Fernet
    recovery_email     text,
    status             text not null default 'active'
                       check (status in ('active', 'suspended', 'banned')),
    notes              text,
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now()
);

-- Perfiles (datos personales, 1 a 1 con managed_accounts)
create table if not exists profiles (
    id          uuid primary key default gen_random_uuid(),
    account_id  uuid references managed_accounts (id) on delete cascade,
    full_name   text,
    phone       text,
    birth_date  date,
    x_username  text,
    fb_username text
);

-- Auditoría (logs de acciones)
create table if not exists audit_logs (
    id             serial primary key,
    account_id     uuid references managed_accounts (id) on delete set null,
    system_user_id uuid references system_users (id) on delete set null,
    action         text not null,   -- 'viewed','updated_status','edited_password','created','deleted'
    details        jsonb,
    created_at     timestamptz not null default now()
);

-- Índices para los filtros más comunes
create index if not exists idx_managed_accounts_status     on managed_accounts (status);
create index if not exists idx_managed_accounts_platform   on managed_accounts (platform);
create index if not exists idx_managed_accounts_created_at on managed_accounts (created_at);
create index if not exists idx_profiles_account_id         on profiles (account_id);
create index if not exists idx_audit_logs_account_id       on audit_logs (account_id);

-- updated_at automático en managed_accounts (search_path fijo por seguridad)
create or replace function set_updated_at()
returns trigger language plpgsql
set search_path = ''
as $$
begin new.updated_at := now(); return new; end $$;

drop trigger if exists trg_managed_accounts_updated_at on managed_accounts;
create trigger trg_managed_accounts_updated_at
  before update on managed_accounts
  for each row execute function set_updated_at();

-- =====================================================================
-- BLINDAJE DE SEGURIDAD
-- El control de acceso lo hace la API (JWT + require_role) y el backend
-- se conecta con la clave service_role (ignora RLS). Aquí se bloquea por
-- completo a los roles públicos anon/authenticated: RLS activo SIN policies
-- + revocación de todos los privilegios. La clave anon/publishable queda
-- inservible contra la base de datos.
-- =====================================================================
alter table public.system_users     enable row level security;
alter table public.managed_accounts enable row level security;
alter table public.profiles         enable row level security;
alter table public.audit_logs       enable row level security;

revoke all privileges on public.system_users     from anon, authenticated;
revoke all privileges on public.managed_accounts from anon, authenticated;
revoke all privileges on public.profiles         from anon, authenticated;
revoke all privileges on public.audit_logs       from anon, authenticated;
revoke all privileges on sequence public.audit_logs_id_seq from anon, authenticated;

-- =====================================================================
-- AUTOMATIZACIÓN: servidores, lotes, gastos y asignaciones
-- (migración del flujo del Excel: "servidor 3", "correos 6 de agosto",
--  "gastos polllitos", "cuentas de compañeros").
-- =====================================================================

-- Servidores / dispositivos de origen de las cuentas
create table if not exists servers (
    id          uuid primary key default gen_random_uuid(),
    name        text not null unique,          -- "Servidor 1", "Dispositivo 3"
    description text,
    created_at  timestamptz not null default now()
);

-- Lotes de cuentas compradas/creadas en una fecha ("correos 6 de agosto")
create table if not exists account_batches (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    purchase_date date,
    notes         text,
    created_at    timestamptz not null default now()
);

-- Gastos ("gastos polllitos"), asociados a un lote
create table if not exists expenses (
    id               uuid primary key default gen_random_uuid(),
    batch_id         uuid references account_batches (id) on delete set null,
    amount           numeric(12, 2) not null check (amount >= 0),
    expense_date     date not null default current_date,
    account_quantity integer not null default 0 check (account_quantity >= 0),
    description      text,
    created_at       timestamptz not null default now()
);

-- Asignaciones cuenta -> usuario (pivote con historial)
create table if not exists assignments (
    id          uuid primary key default gen_random_uuid(),
    account_id  uuid not null references managed_accounts (id) on delete cascade,
    user_id     uuid not null references system_users (id)     on delete cascade,
    assigned_by uuid references system_users (id) on delete set null,
    assigned_at timestamptz not null default now(),
    unique (account_id, user_id)   -- evita duplicar la misma asignación
);

-- FK directas de cuenta a servidor y lote
alter table managed_accounts
    add column if not exists server_id uuid references servers (id)         on delete set null,
    add column if not exists batch_id  uuid references account_batches (id) on delete set null;

-- Índices de las nuevas relaciones
create index if not exists idx_managed_accounts_server_id on managed_accounts (server_id);
create index if not exists idx_managed_accounts_batch_id  on managed_accounts (batch_id);
create index if not exists idx_expenses_batch_id          on expenses (batch_id);
create index if not exists idx_assignments_account_id     on assignments (account_id);
create index if not exists idx_assignments_user_id        on assignments (user_id);

-- Mismo blindaje: RLS activo sin policies + revocación total a roles públicos
alter table public.servers         enable row level security;
alter table public.account_batches enable row level security;
alter table public.expenses        enable row level security;
alter table public.assignments     enable row level security;

revoke all privileges on public.servers         from anon, authenticated;
revoke all privileges on public.account_batches from anon, authenticated;
revoke all privileges on public.expenses        from anon, authenticated;
revoke all privileges on public.assignments     from anon, authenticated;
