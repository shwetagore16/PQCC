"""
dev_server.py — Standalone FastAPI dev server for local testing WITHOUT databases.

Starts a fully-functional FastAPI app that:
  • Exposes all REST endpoints (assets, compliance, /health, /docs)
  • Skips PostgreSQL + Neo4j connection at startup (no crashes)
  • Serves Swagger UI at http://localhost:8000/api/v1/docs
  • Works with zero infrastructure — only Python required

Run:
    cd backend
    python dev_server.py
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Any

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ── Settings ──────────────────────────────────────────────────────────────────
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(debug=True)
log = structlog.get_logger()


# ── Dev lifespan (no DB connections) ─────────────────────────────────────────
@asynccontextmanager
async def dev_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info(
        "🚀 PQSS dev server starting",
        version=settings.PROJECT_VERSION,
        docs=f"http://localhost:8000{settings.API_V1_STR}/docs",
        note="DB connections SKIPPED — running in stub mode",
    )
    yield
    log.info("🛑 PQSS dev server stopped")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=f"{settings.PROJECT_NAME} [DEV]",
    version=settings.PROJECT_VERSION,
    description=(
        "**Development mode** — databases skipped. "
        "All API endpoints available for testing against stub data.\n\n"
        "Post-Quantum Cryptography readiness platform for the PSB Hackathon 2026."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=dev_lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start    = time.perf_counter()
        response = await call_next(request)
        ms       = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{ms:.1f}"
        return response


app.add_middleware(TimingMiddleware)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"], include_in_schema=False)
async def health() -> dict:
    return {
        "status":  "healthy",
        "mode":    "dev-stub",
        "version": settings.PROJECT_VERSION,
    }


# ── Stub routers (no DB required) ─────────────────────────────────────────────

from fastapi import APIRouter
from pydantic import BaseModel, Field
import random

stub = APIRouter(prefix=settings.API_V1_STR, tags=["Stub Data"])


# ── HNDL Scoring stub ─────────────────────────────────────────────────────────
@stub.post("/hndl/score", summary="Compute HNDL risk score for an algorithm")
async def hndl_score(body: dict) -> dict:
    """
    Computes a real HNDL score using the ml_engine scorer.
    Fallback to synthetic data if ml_engine not installed.
    """
    algo     = body.get("algo", "rsa-2048")
    key_bits = int(body.get("key_bits", 2048))
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from ml_engine.hndl_scorer import HNDLScorer
        scorer = HNDLScorer()
        result = scorer.score(algo=algo, key_bits=key_bits)
        return result.model_dump()
    except Exception as e:
        # Synthetic fallback
        return {
            "algo":         algo,
            "key_bits":     key_bits,
            "quantum_safe": False,
            "expiry_year":  2030,
            "hndl_score":   round(random.uniform(5.0, 9.5), 2),
            "agility_score": round(random.uniform(2.0, 7.0), 2),
            "risk_band":    "high",
            "note":         f"synthetic (ml_engine not available: {e})",
        }


# ── Compliance label stub ──────────────────────────────────────────────────────
@stub.post("/compliance/label", summary="Label asset PQC compliance")
async def compliance_label(body: dict) -> dict:
    algorithms = body.get("algorithms", ["rsa-2048"])
    host       = body.get("host", "example.pnb.co.in")
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from app.compliance.labeling import PQCComplianceLabeler
        labeler = PQCComplianceLabeler()
        result  = labeler.label_asset(algorithms=algorithms, host=host)
        return result.model_dump()
    except Exception as e:
        return {
            "host":          host,
            "quantum_label": "quantum_vulnerable",
            "algorithms":    algorithms,
            "note":          f"synthetic (compliance module error: {e})",
        }


# ── Assets stub ───────────────────────────────────────────────────────────────
_SAMPLE_ASSETS = [
    {
        "id": str(uuid.uuid4()), "host": "api.pnb.co.in",
        "risk_band": "critical", "hndl_score": 8.4, "algo": "RSA-2048",
        "quantum_label": "quantum_vulnerable",
    },
    {
        "id": str(uuid.uuid4()), "host": "netbanking.pnb.co.in",
        "risk_band": "high", "hndl_score": 6.7, "algo": "ECDH-P256",
        "quantum_label": "quantum_vulnerable",
    },
    {
        "id": str(uuid.uuid4()), "host": "mobile.pnb.co.in",
        "risk_band": "medium", "hndl_score": 4.2, "algo": "X25519Kyber768",
        "quantum_label": "pqc_ready",
    },
    {
        "id": str(uuid.uuid4()), "host": "cdn.pnb.co.in",
        "risk_band": "low", "hndl_score": 1.1, "algo": "ML-KEM-768",
        "quantum_label": "fully_quantum_safe",
    },
]


@stub.get("/assets", summary="List assets (stub)")
async def list_assets(skip: int = 0, limit: int = 20) -> dict:
    return {
        "total": len(_SAMPLE_ASSETS),
        "items": _SAMPLE_ASSETS[skip : skip + limit],
    }


@stub.get("/assets/{asset_id}", summary="Get asset by ID (stub)")
async def get_asset(asset_id: str) -> dict:
    for a in _SAMPLE_ASSETS:
        if a["id"] == asset_id:
            return a
    return {"error": "not found", "id": asset_id}


# ── Attack path stub ──────────────────────────────────────────────────────────
@stub.get("/attack-paths", summary="Sample GNN attack paths (stub)")
async def attack_paths() -> dict:
    return {
        "paths": [
            {
                "rank": 1,
                "nodes": ["Internet", "LoadBalancer:api.pnb.co.in", "WebServer:app01", "APIServer:auth", "Database:pg-primary"],
                "total_risk": 8.9,
                "cvss_score": 9.1,
                "gnn_confidence": 0.87,
            },
            {
                "rank": 2,
                "nodes": ["Internet", "LoadBalancer:api.pnb.co.in", "WebServer:app02", "APIServer:payments"],
                "total_risk": 6.4,
                "cvss_score": 7.8,
                "gnn_confidence": 0.72,
            },
        ]
    }


# ── Forecast stub ─────────────────────────────────────────────────────────────
@stub.get("/forecast", summary="HNDL exposure forecast (stub P10/P50/P90)")
async def forecast() -> dict:
    import datetime
    bands = []
    base  = 5.0
    today = datetime.date.today()
    for q in range(20):
        date = (today + datetime.timedelta(days=q * 90)).isoformat()
        p50  = round(min(10, base + q * 0.22), 2)
        bands.append({"date": date, "p10": round(p50 - 0.8, 2), "p50": p50, "p90": round(p50 + 1.2, 2)})
    return {
        "scenario": "do_nothing",
        "monte_carlo": {
            "median_exposure_year": 2033.4,
            "p10_exposure_year":    2031.2,
            "p90_exposure_year":    2036.8,
            "prob_breach_before_2030": 0.12,
            "prob_breach_before_2035": 0.64,
        },
        "prophet_forecast": bands,
    }


app.include_router(stub)


# ── Exception handler ─────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def generic_exception(request: Request, exc: Exception) -> JSONResponse:
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n" + "═" * 60)
    print("  🔐 Quantum-Proof Systems Scanner — Dev Server")
    print(f"  📖 Swagger UI → http://localhost:8000{settings.API_V1_STR}/docs")
    print(f"  ❤  Health    → http://localhost:8000/health")
    print("  ℹ  Mode: no-database stub (all endpoints available)")
    print("═" * 60 + "\n")
    uvicorn.run(
        "dev_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
