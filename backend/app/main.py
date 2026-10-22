"""FastAPI application entry point.

Builds the app via a factory so tests can construct isolated instances. Wires
CORS (explicit origins only), a consistent error envelope, structured logging,
and the router set. Scanner/scan routers are added in later phases; the health
router is live now.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.routes import findings, health, reports, scans, ws
from app.config import settings
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks."""
    configure_logging()
    logger.info(
        "starting cawasma backend env=%s debug=%s", settings.ENVIRONMENT, settings.DEBUG
    )
    yield
    logger.info("shutting down cawasma backend")


def _error_body(code: str, message: str) -> dict:
    """Build the standard error envelope (spec section 44)."""
    return {"success": False, "error": {"code": code, "message": message}}


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="CAWASMA — Context-Aware Web & API Security Misconfiguration Analyzer",
        description=(
            "Defensive black-box security misconfiguration analyzer. "
            "REST + WebSocket backend for a separate JavaScript frontend."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # --- CORS: explicit origins only, never "*" --------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # --- Consistent error handling ---------------------------------------
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
        }.get(exc.status_code, "HTTP_ERROR")
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(
            status_code=exc.status_code, content=_error_body(code, detail)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content=_error_body(
                "VALIDATION_ERROR", "Request validation failed."
            )
            | {"details": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Never leak stack traces to clients (spec section 27/44).
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_error_body(
                "INTERNAL_ERROR", "An internal error occurred."
            ),
        )

    # --- Routers ---------------------------------------------------------
    app.include_router(health.router)
    app.include_router(scans.router)
    app.include_router(findings.router)
    app.include_router(reports.router)
    app.include_router(ws.router)

    return app


app = create_app()
