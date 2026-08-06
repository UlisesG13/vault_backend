"""Punto de entrada de la API FastAPI. Ejecuta: uvicorn src.main:app --reload"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import get_settings
from .domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DomainError,
    DuplicateEmailError,
    InvalidCredentialsError,
    NotFoundError,
)
from .api.routers import accounts_router, admin_router, auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("vault-backend")

app = FastAPI(
    title="Vault Backend — Gestor de Cuentas",
    description="API REST para gestionar credenciales de cuentas digitales.",
    version="1.0.0",
)

# CORS restringido a los orígenes de CORS_ORIGINS (.env). La API usa Bearer
# tokens (no cookies), por eso allow_credentials=False.
_origins = get_settings().cors_origin_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router.router)
app.include_router(accounts_router.router)
app.include_router(admin_router.router)


# ---------- Manejo global de errores de dominio ----------
# Cada excepción de negocio se traduce a un código HTTP y un cuerpo uniforme.
_STATUS_MAP: dict[type[DomainError], int] = {
    NotFoundError: 404,
    DuplicateEmailError: 409,
    InvalidCredentialsError: 401,
    AuthenticationError: 401,
    AuthorizationError: 403,
}


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status_code = next(
        (code for typ, code in _STATUS_MAP.items() if isinstance(exc, typ)), 400
    )
    if status_code >= 500:
        logger.exception("Error de dominio no controlado: %s", exc)
    else:
        logger.info("%s en %s: %s", type(exc).__name__, request.url.path, exc)
    return JSONResponse(
        status_code=status_code,
        content={"error": type(exc).__name__, "detail": str(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "detail": "Ocurrió un error inesperado"},
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
