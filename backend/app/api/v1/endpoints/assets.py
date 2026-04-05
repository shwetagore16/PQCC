"""
api/v1/endpoints/assets.py — Asset Discovery & Ingestion REST endpoints.

Endpoints:
  POST   /assets/seed-domains       — Ingest seed domains & optionally trigger scans
  GET    /assets                    — Paginated list of all known assets
  GET    /assets/{asset_id}         — Retrieve a single asset by UUID
  POST   /assets/{asset_id}/scan    — On-demand scan trigger for a specific asset
  POST   /assets/bulk-scan          — Trigger scans across a filtered asset subset
  DELETE /assets/{asset_id}         — Soft-delete (exclude) an asset
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.base import get_db
from app.db.models.asset import AssetStatus, AssetType, MasterAsset
from app.schemas.asset import (
    AssetListResponse,
    AssetResponse,
    BulkScanRequest,
    ScanJobResponse,
    SeedDomainIngestionRequest,
    SeedDomainIngestionResponse,
    TriggerScanRequest,
)
from app.workers.tasks.discovery import (
    ingest_seed_domain,
    run_amass_discovery,
    run_shodan_query,
)

router = APIRouter(prefix="/assets", tags=["Asset Discovery"])


# ── POST /assets/seed-domains ────────────────────────────────────────────────

@router.post(
    "/seed-domains",
    response_model=SeedDomainIngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest seed domains and optionally trigger discovery scans",
)
async def ingest_seed_domains(
    payload: SeedDomainIngestionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SeedDomainIngestionResponse:
    """
    Accepts a list of root domains, persists each as a pending MasterAsset,
    and — when `auto_scan` is True — dispatches Amass + Shodan discovery tasks.

    Returns a 202 Accepted with the created asset rows and Celery task IDs.
    """
    task_ids: list[str] = []
    created_assets: list[MasterAsset] = []

    for domain in payload.domains:
        # Synchronous DB write inside the request (fast, < 5 ms per row)
        existing = await db.execute(
            select(MasterAsset).where(
                MasterAsset.asset_value == domain,
                MasterAsset.asset_type == AssetType.DOMAIN,
            )
        )
        asset = existing.scalar_one_or_none()

        if asset is None:
            asset = MasterAsset(
                asset_type=AssetType.DOMAIN,
                asset_value=domain,
                organization=payload.organization,
                seed_domain=domain,
                status=AssetStatus.PENDING,
                tags=payload.tags or [],
            )
            db.add(asset)
            await db.flush()   # get the generated id without full commit
            logger.info("asset_created", domain=domain, asset_id=str(asset.id))

        created_assets.append(asset)

        if payload.auto_scan:
            amass_task = run_amass_discovery.apply_async(
                args=[domain, payload.organization],
                queue="discovery",
            )
            shodan_task = run_shodan_query.apply_async(
                args=[domain, payload.organization],
                queue="discovery",
            )
            task_ids.extend([amass_task.id, shodan_task.id])

    await db.commit()
    for asset in created_assets:
        await db.refresh(asset)

    return SeedDomainIngestionResponse(
        ingested_count=len(created_assets),
        task_ids=task_ids,
        assets=[AssetResponse.model_validate(a) for a in created_assets],
    )


# ── GET /assets ──────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=AssetListResponse,
    summary="List all known assets with filtering and pagination",
)
async def list_assets(
    db: Annotated[AsyncSession, Depends(get_db)],
    asset_type: AssetType | None = Query(None),
    status: AssetStatus | None = Query(None),
    seed_domain: str | None = Query(None),
    min_risk: float | None = Query(None, ge=0.0, le=10.0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> AssetListResponse:
    """
    Return a paginated list of assets.  Supports filtering by type, status,
    seed domain, and minimum PQC risk score.
    """
    stmt = select(MasterAsset)

    if asset_type:
        stmt = stmt.where(MasterAsset.asset_type == asset_type)
    if status:
        stmt = stmt.where(MasterAsset.status == status)
    if seed_domain:
        stmt = stmt.where(MasterAsset.seed_domain == seed_domain.lower())
    if min_risk is not None:
        stmt = stmt.where(MasterAsset.risk_score >= min_risk)

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size).order_by(MasterAsset.risk_score.desc().nullslast())
    result = await db.execute(stmt)
    assets = result.scalars().all()

    return AssetListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AssetResponse.model_validate(a) for a in assets],
    )


# ── POST /assets/bulk-scan ───────────────────────────────────────────────────
# NOTE: This MUST come before /{asset_id} routes to prevent "bulk-scan" from being
# matched as an asset_id parameter in FastAPI's route matching

@router.post(
    "/bulk-scan",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger scans across a filtered asset subset",
)
async def bulk_scan(
    payload: BulkScanRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    from app.workers.tasks.tls_scan import run_tls_scan  # noqa: PLC0415

    stmt = select(MasterAsset)
    if payload.asset_ids:
        stmt = stmt.where(MasterAsset.id.in_(payload.asset_ids))
    else:
        if payload.filter_by_status:
            stmt = stmt.where(MasterAsset.status.in_(payload.filter_by_status))
        if payload.filter_by_type:
            stmt = stmt.where(MasterAsset.asset_type.in_(payload.filter_by_type))

    stmt = stmt.limit(payload.max_assets)
    result = await db.execute(stmt)
    assets = result.scalars().all()

    dispatched = 0
    for asset in assets:
        for scan_type in payload.scan_types:
            if scan_type == "tls":
                run_tls_scan.apply_async(
                    args=[str(asset.id), asset.asset_value],
                    queue="scanning",
                )
                dispatched += 1
        asset.status = AssetStatus.SCANNING

    await db.commit()
    logger.info("bulk_scan_dispatched", count=dispatched)
    return {"dispatched_tasks": dispatched, "assets_targeted": len(assets)}


# ── GET /assets/{asset_id} ───────────────────────────────────────────────────

@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Retrieve a single asset by UUID",
)
async def get_asset(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssetResponse:
    result = await db.execute(
        select(MasterAsset).where(MasterAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found.",
        )
    return AssetResponse.model_validate(asset)


# ── POST /assets/{asset_id}/scan ─────────────────────────────────────────────

@router.post(
    "/{asset_id}/scan",
    response_model=ScanJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an on-demand scan for a specific asset",
)
async def trigger_asset_scan(
    asset_id: uuid.UUID,
    payload: TriggerScanRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScanJobResponse:
    result = await db.execute(
        select(MasterAsset).where(MasterAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found.")

    # Import scanning tasks lazily to avoid circular imports
    from app.workers.tasks.tls_scan import run_tls_scan  # noqa: PLC0415

    task_ids: list[str] = []
    for scan_type in payload.scan_types:
        if scan_type == "tls":
            t = run_tls_scan.apply_async(
                args=[str(asset_id), asset.asset_value],
                kwargs={"priority": payload.priority},
                queue="scanning",
                priority=payload.priority,
            )
            task_ids.append(t.id)
        elif scan_type in ("amass", "shodan"):
            if asset.seed_domain:
                fn = run_amass_discovery if scan_type == "amass" else run_shodan_query
                t = fn.apply_async(
                    args=[asset.seed_domain, asset.organization],
                    queue="discovery",
                )
                task_ids.append(t.id)

    # Update asset status to SCANNING
    asset.status = AssetStatus.SCANNING
    await db.commit()

    return ScanJobResponse(
        task_id=task_ids[0] if task_ids else "no_tasks_dispatched",
        asset_id=asset_id,
        scan_types=payload.scan_types,
        status="queued",
        message=f"Dispatched {len(task_ids)} scan task(s).",
    )


# ── DELETE /assets/{asset_id} ────────────────────────────────────────────────

@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclude an asset from future scans (soft delete)",
)
async def exclude_asset(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(
        select(MasterAsset).where(MasterAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found.")
    asset.status = AssetStatus.EXCLUDED
    await db.commit()
