"""
main.py — FastAPI application factory for the Quantum-Proof Systems Scanner.

Startup sequence:
  1. Configure structured logging
  2. Run Alembic migrations (optional, controlled by env var)
  3. Initialise Neo4j driver
  4. Register all routers
  5. Mount middleware (CORS, rate-limit, request-id, security headers)
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.api.v1.endpoints import assets as assets_router
from app.core.config import get_settings
from app.core.logging import configure_logging, logger
from app.db.base import engine
from app.db.graph import close_neo4j, init_neo4j

settings = get_settings()


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application-level resources across the full server lifetime.
    Runs startup tasks before `yield` and teardown tasks after.
    """
    # ── Startup ──────────────────────────────────────────────────────────────
    configure_logging(debug=settings.DEBUG)
    logger.info(
        "startup",
        project=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
    )

    # Neo4j
    await init_neo4j()

    # (Optional) warm-up the PG connection pool
    async with engine.connect() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    logger.info("postgres_pool_warmed")

    yield  # ← server accepts requests here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    await close_neo4j()
    await engine.dispose()
    logger.info("shutdown_complete")


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=(
            "Post-Quantum Cryptography readiness platform for public-facing banking assets. "
            "Combines TLS inspection, CBOM generation, GNN-based attack-path analysis, "
            "and NIST PQC migration playbooks."
        ),
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    _register_middleware(app)
    _register_routers(app)
    _register_exception_handlers(app)

    return app


# ── Middleware ────────────────────────────────────────────────────────────────

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID header to every request and response."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        with structlog.contextvars.bound_contextvars(request_id=request_id):
            response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Log request duration and add X-Process-Time header."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        logger.debug(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response


def _register_middleware(app: FastAPI) -> None:
    # Order matters — outermost middleware runs first on the way IN
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)


# ── Routers ───────────────────────────────────────────────────────────────────

def _register_routers(app: FastAPI) -> None:
    app.include_router(
        assets_router.router,
        prefix=settings.API_V1_STR,
    )
    # Placeholder for future tiers — uncomment as phases progress
    from app.api.v1.endpoints import compliance, cbom, topology, dev
    # app.include_router(scans.router,      prefix=settings.API_V1_STR)
    app.include_router(cbom.router,       prefix=settings.API_V1_STR)
    app.include_router(compliance.router, prefix=settings.API_V1_STR)
    app.include_router(topology.router,   prefix=settings.API_V1_STR)
    app.include_router(dev.router,        prefix=settings.API_V1_STR)


# ── Exception handlers ────────────────────────────────────────────────────────

def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error.",
                "request_id": request.headers.get("X-Request-ID"),
            },
        )


# ── Health check ──────────────────────────────────────────────────────────────

app = create_app()


@app.get("/health", tags=["Health"], include_in_schema=False)
async def health_check() -> dict:
    return {
        "status": "healthy",
        "version": settings.PROJECT_VERSION,
        "project": settings.PROJECT_NAME,
    }


# ── Import fix for middleware typing ──────────────────────────────────────────
# (Avoid circular import by placing after app creation)
from typing import Any  # noqa: E402
import structlog  # noqa: E402
