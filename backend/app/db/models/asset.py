"""
db/models/asset.py — Master Asset Matrix ORM model.

Represents every discovered public-facing banking asset (domain, IP, URL, cert).
JSONB columns store flexible, schema-less metadata without losing query-ability.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssetType(str, enum.Enum):
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    URL = "url"
    CERTIFICATE = "certificate"
    API_ENDPOINT = "api_endpoint"
    LOAD_BALANCER = "load_balancer"


class AssetStatus(str, enum.Enum):
    PENDING = "pending"          # Discovered, not yet scanned
    SCANNING = "scanning"        # Active scan in progress
    SCANNED = "scanned"          # At least one scan completed
    ERROR = "error"              # Last scan failed
    EXCLUDED = "excluded"        # Explicitly excluded from scanning


class MasterAsset(Base):
    """
    Master Asset Matrix — central registry of all discovered public-facing assets.

    One asset row may link to many TLS scans, CBOM records, and ports.
    The `metadata_` JSONB column stores discovery-source-specific fields
    (e.g. Shodan banners, Amass relationships) without schema migrations.
    """

    __tablename__ = "master_assets"
    __table_args__ = (
        UniqueConstraint("asset_value", "asset_type", name="uq_asset_value_type"),
        Index("ix_master_assets_asset_type", "asset_type"),
        Index("ix_master_assets_status", "status"),
        Index("ix_master_assets_risk_score", "risk_score"),
        Index(
            "ix_master_assets_metadata_gin",
            "metadata_",
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Surrogate PK — UUIDv4",
    )
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type_enum"),
        nullable=False,
    )
    asset_value: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="The raw asset identifier (FQDN, IPv4/v6, URL …)",
    )
    organization: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Owning organization / business unit",
    )
    seed_domain: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Root domain from which this asset was discovered",
    )
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status_enum"),
        nullable=False,
        default=AssetStatus.PENDING,
        server_default="pending",
    )
    risk_score: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="Composite PQC risk score [0.0 – 10.0]",
    )
    tags: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of labels, e.g. ["internet-facing", "pci-scope"]',
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        comment="Free-form discovery metadata (Shodan, Amass, Censys …)",
    )
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_scanned: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────────
    tls_scans: Mapped[list["TLSScanResult"]] = relationship(
        "TLSScanResult",
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cbom_records: Mapped[list["CBOMRecord"]] = relationship(
        "CBOMRecord",
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<MasterAsset id={self.id} type={self.asset_type} value={self.asset_value!r}>"
