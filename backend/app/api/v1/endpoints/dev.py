"""
api/v1/endpoints/dev.py — Development and Simulation utilities.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.workers.tasks.scans import run_tls_scan
from app.workers.tasks.discovery import ingest_seed_domain

router = APIRouter(prefix="/dev", tags=["Dev/Simulation"])

@router.post("/simulate-scan")
async def simulate_scan(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Simulate a scheduled global scan.
    Triggers discovery and TLS scanning for mock targets.
    """
    targets = [
        "api.prod.gateway.com",
        "legacy.vault-01.internal",
        "kyber-demo.pnc.bank",
    ]
    
    # In a real app we would query the DB for assets, but here we simulate a "Seed" discovery first
    for target in targets:
        # Simulate discovery
        background_tasks.add_task(ingest_seed_domain, target)
        
    return {"status": "Simulation triggered", "targets": targets}


@router.get("/forecast")
async def forecast() -> dict:
    """
    HNDL exposure forecast with P10, P50, P90 projections.
    Returns Monte Carlo simulation results for quantum threat timeline.
    """
    # Mock forecast data simulating Prophet output
    bands = [
        {"year": 2026, "month": i, "p10": 65.0 + i*1.5, "p50": 75.0 + i*1.2, "p90": 85.0 + i*0.8}
        for i in range(1, 13)
    ]
    bands.extend([
        {"year": 2027, "month": i, "p10": 83.0 + i*1.0, "p50": 87.0 + i*0.8, "p90": 92.0 + i*0.5}
        for i in range(1, 13)
    ])
    
    return {
        "crqc_arrival_model": "log-normal(μ=12 years, σ=3)",
        "crqc_p50_year": 2036,
        "bands": bands,
        "monte_carlo": {
            "prob_breach_before_2030": 0.15,
            "prob_breach_before_2035": 0.42,
            "prob_breach_before_2040": 0.78,
            "median_breach_year": 2036,
        },
        "asset_risk_trajectory": [
            {
                "asset_id": "asset-001",
                "name": "vpn.pnb.bank",
                "current_risk": 85,
                "pqc_ready_date": "2026-Q2",
                "projected_risk_2030": 45,
                "projected_risk_2035": 20,
            },
            {
                "asset_id": "asset-002",
                "name": "api.gateway.pnb",
                "current_risk": 62,
                "pqc_ready_date": "2026-Q4",
                "projected_risk_2030": 32,
                "projected_risk_2035": 10,
            },
        ],
    }
