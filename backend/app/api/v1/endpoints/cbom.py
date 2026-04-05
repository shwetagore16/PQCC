"""
api/v1/endpoints/cbom.py — Cryptography Bill of Materials (CBOM) API endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models.cbom import CBOMRecord, CryptoCategory, PQCStatus
from app.services.cbom_service import CBOMService

router = APIRouter(prefix="/cbom", tags=["CBOM"])

@router.get("/", response_model=list[dict[str, Any]])
async def list_cbom_records(
    asset_id: uuid.UUID | None = Query(None, description="Filter by asset ID"),
    category: CryptoCategory | None = Query(None, description="Filter by crypto category"),
    pqc_status: PQCStatus | None = Query(None, description="Filter by PQC safety status"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Retrieve CBOM records with optional filtering.
    """
    query = select(CBOMRecord)
    if asset_id:
        query = query.where(CBOMRecord.asset_id == asset_id)
    if category:
        query = query.where(CBOMRecord.category == category)
    if pqc_status:
        query = query.where(CBOMRecord.pqc_status == pqc_status)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Simple JSON conversion logic (would use Pydantic models in real impl)
    return [
        {
            "id": str(r.id),
            "asset_id": str(r.asset_id),
            "algorithm_name": r.algorithm_name,
            "category": r.category,
            "pqc_status": r.pqc_status,
            "usage_context": r.usage_context,
            "quantum_risk_score": r.quantum_risk_score,
            "replacement_algorithm": r.replacement_algorithm,
            "last_confirmed": r.last_confirmed.isoformat() if r.last_confirmed else None,
        }
        for r in records
    ]

@router.get("/{asset_id}", response_model=list[dict[str, Any]])
async def get_asset_cbom(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Get the full CBOM for a specific asset.
    """
    records = await CBOMService.get_cbom_for_asset(db, asset_id)
    return [
        {
            "id": str(r.id),
            "algorithm_name": r.algorithm_name,
            "category": r.category,
            "pqc_status": r.pqc_status,
            "usage_context": r.usage_context,
        }
        for r in records
    ]
