"""
schemas/asset.py — Pydantic v2 request/response schemas for the Asset Discovery API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ── Enums (re-export from ORM for API contracts) ────────────────────────────
from app.db.models.asset import AssetStatus, AssetType  # noqa: E402


# ── Shared base ──────────────────────────────────────────────────────────────

class AssetBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_type: AssetType
    asset_value: str = Field(..., max_length=2048)
    organization: str | None = Field(None, max_length=512)
    seed_domain: str | None = Field(None, max_length=512)
    tags: list[str] | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


# ── Request schemas ──────────────────────────────────────────────────────────

class SeedDomainIngestionRequest(BaseModel):
    """
    POST /api/v1/assets/seed-domains
    Accepts one or more seed domains to kick off discovery.
    """
    domains: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of root domains to discover assets from",
        examples=[["pnb.co.in", "onlinesbi.com"]],
    )
    organization: str | None = Field(None, max_length=512)
    tags: list[str] | None = None
    auto_scan: bool = Field(
        default=True,
        description="Immediately trigger Amass + Shodan scan tasks after ingestion",
    )

    @field_validator("domains", mode="before")
    @classmethod
    def strip_and_lower(cls, v: list[str]) -> list[str]:
        return [d.strip().lower() for d in v if d.strip()]


class TriggerScanRequest(BaseModel):
    """
    POST /api/v1/assets/{asset_id}/scan
    Trigger an on-demand scan for a specific asset.
    """
    scan_types: list[str] = Field(
        default=["tls", "amass", "shodan"],
        description="Scan modules to run: 'tls', 'amass', 'shodan', 'masscan', 'nmap'",
    )
    priority: int = Field(default=5, ge=1, le=10, description="Task priority [1-lo … 10-hi]")
    notify_webhook: str | None = Field(
        None, description="Optional webhook URL to call on completion"
    )


class BulkScanRequest(BaseModel):
    """
    POST /api/v1/assets/bulk-scan
    Trigger scans across a filtered subset of assets.
    """
    asset_ids: list[uuid.UUID] | None = Field(
        None, description="Explicit list of asset UUIDs; if None, uses filters below"
    )
    filter_by_status: list[AssetStatus] | None = None
    filter_by_type: list[AssetType] | None = None
    scan_types: list[str] = Field(default=["tls"])
    max_assets: int = Field(default=100, ge=1, le=500)


# ── Response schemas ─────────────────────────────────────────────────────────

class AssetResponse(AssetBase):
    id: uuid.UUID
    status: AssetStatus
    risk_score: float | None
    first_seen: datetime
    last_scanned: datetime | None
    created_at: datetime
    updated_at: datetime


class SeedDomainIngestionResponse(BaseModel):
    ingested_count: int
    task_ids: list[str] = Field(
        description="Celery task IDs for the triggered discovery jobs"
    )
    assets: list[AssetResponse]

    model_config = ConfigDict(from_attributes=True)


class ScanJobResponse(BaseModel):
    task_id: str
    asset_id: uuid.UUID
    scan_types: list[str]
    status: str = "queued"
    message: str


class AssetListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AssetResponse]

    model_config = ConfigDict(from_attributes=True)
