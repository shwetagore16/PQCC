"""
db/models/tls_scan.py — TLS Scan Results ORM model.

Captures the complete cryptographic profile of a TLS handshake:
  • Protocol version(s) supported
  • Cipher suites (symmetric + key exchange algorithms)
  • Certificate chain metadata
  • HNDL (Harvest Now, Decrypt Later) risk score
  • Raw SSLyze / ZGrab2 output (JSONB)
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TLSVersion(str, enum.Enum):
    SSL_2_0 = "SSLv2"
    SSL_3_0 = "SSLv3"
    TLS_1_0 = "TLSv1.0"
    TLS_1_1 = "TLSv1.1"
    TLS_1_2 = "TLSv1.2"
    TLS_1_3 = "TLSv1.3"


class ScanSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TLSScanResult(Base):
    """
    TLS Scan Results — one row per scan-run per asset.

    Key design decisions:
    - `cipher_suites` stores the complete ordered list of offered suites
      as a JSONB array; each element is a dict with algorithm, key_size, pqc_safe.
    - `certificate_chain` stores the full PEM / parsed chain metadata in JSONB
      to avoid a separate table while keeping JSON querying.
    - `hndl_score` is a float [0–10] produced by the AI engine.
    - `raw_output` archives the verbatim tool output for auditability / re-analysis.
    """

    __tablename__ = "tls_scan_results"
    __table_args__ = (
        Index("ix_tls_scan_results_asset_id", "asset_id"),
        Index("ix_tls_scan_results_scanned_at", "scanned_at"),
        Index("ix_tls_scan_results_severity", "severity"),
        Index("ix_tls_scan_results_hndl_score", "hndl_score"),
        Index(
            "ix_tls_scan_results_cipher_suites_gin",
            "cipher_suites",
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("master_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    scan_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Reference to the Celery task / scan job that produced this result",
    )

    # ── TLS profile ──────────────────────────────────────────────────────────
    host: Mapped[str] = mapped_column(String(512), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=443)
    highest_tls_version: Mapped[TLSVersion | None] = mapped_column(
        Enum(TLSVersion, name="tls_version_enum"),
        nullable=True,
    )
    supports_pqc_kem: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if server negotiated a PQC KEM (e.g. X25519Kyber768)",
    )
    cipher_suites: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="[{name, key_exchange, auth, symmetric, key_size, pqc_safe}, …]",
    )
    certificate_chain: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Parsed cert chain: [{subject, issuer, not_after, sig_alg, key_alg, key_size}, …]",
    )
    leaf_cert_sig_algorithm: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="e.g. 'sha256WithRSAEncryption', 'ecdsa-with-SHA384'",
    )
    leaf_cert_key_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="RSA modulus bits / EC curve bits of the leaf certificate key",
    )
    leaf_cert_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Risk scoring ─────────────────────────────────────────────────────────
    severity: Mapped[ScanSeverity] = mapped_column(
        Enum(ScanSeverity, name="scan_severity_enum"),
        nullable=False,
        default=ScanSeverity.INFO,
    )
    hndl_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Harvest-Now-Decrypt-Later risk score [0.0 – 10.0]",
    )
    vulnerability_ids: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="CVE / advisory IDs discovered during scan",
    )

    # ── Raw output ───────────────────────────────────────────────────────────
    scan_tool: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Tool used: 'sslyze', 'zgrab2', 'openssl'",
    )
    raw_output: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Verbatim JSON output from the scanning tool",
    )
    scan_duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Wall-clock time for this scan in milliseconds",
    )

    # ── Timestamps ───────────────────────────────────────────────────────────
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────────
    asset: Mapped["MasterAsset"] = relationship(
        "MasterAsset",
        back_populates="tls_scans",
    )

    def __repr__(self) -> str:
        return (
            f"<TLSScanResult id={self.id} asset={self.asset_id}"
            f" host={self.host}:{self.port} severity={self.severity}>"
        )
