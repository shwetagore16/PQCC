"""
db/models/cbom.py — Cryptography Bill of Materials (CBOM) ORM model.

A CBOM record catalogues every cryptographic primitive/algorithm detected
on an asset — analogous to a Software BOM (SBOM) but focused entirely on
cryptography.  The schema follows the CycloneDX CBOM specification draft.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CryptoCategory(str, enum.Enum):
    """Top-level classification of the cryptographic primitive."""
    KEY_EXCHANGE = "key_exchange"            # DH, ECDH, X25519, Kyber …
    DIGITAL_SIGNATURE = "digital_signature"  # RSA-PSS, ECDSA, Dilithium …
    SYMMETRIC_CIPHER = "symmetric_cipher"    # AES-128-GCM, ChaCha20-Poly1305 …
    HASH = "hash"                            # SHA-256, SHA3-256 …
    MAC = "mac"                              # HMAC-SHA256, GHASH …
    KEY_DERIVATION = "key_derivation"        # HKDF, PBKDF2 …
    PRNG = "prng"                            # DRBG, Fortuna …
    CERTIFICATE = "certificate"              # X.509 meta
    PROTOCOL = "protocol"                    # TLS 1.3, SSH, DTLS …
    OTHER = "other"


class PQCStatus(str, enum.Enum):
    """Post-quantum safety classification for this algorithm."""
    SAFE = "safe"                 # NIST PQC finalist / approved
    HYBRID = "hybrid"             # Classical + PQC hybrid
    CLASSICAL = "classical"       # Classical only (quantum-vulnerable)
    DEPRECATED = "deprecated"     # Already broken / officially deprecated
    UNKNOWN = "unknown"


class CBOMRecord(Base):
    """
    CBOM Record — one row per unique (asset, algorithm, usage_context) triple.

    Design notes:
    - `algorithm_parameters` JSONB stores algorithm-specific details
      (key length, curve name, padding scheme …) without extra tables.
    - `detection_sources` JSONB array records every tool/method that found
      this crypto usage.
    - `migration_recommendation` JSONB stores the AI-generated playbook
      step for replacing this algorithm.
    """

    __tablename__ = "cbom_records"
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "algorithm_oid",
            "usage_context",
            name="uq_cbom_asset_algorithm_context",
        ),
        Index("ix_cbom_records_asset_id", "asset_id"),
        Index("ix_cbom_records_pqc_status", "pqc_status"),
        Index("ix_cbom_records_category", "category"),
        Index("ix_cbom_records_quantum_risk_score", "quantum_risk_score"),
        Index(
            "ix_cbom_records_algorithm_parameters_gin",
            "algorithm_parameters",
            postgresql_using="gin",
        ),
        Index(
            "ix_cbom_records_detection_sources_gin",
            "detection_sources",
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
    scan_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tls_scan_results.id", ondelete="SET NULL"),
        nullable=True,
        comment="Source TLS scan if this CBOM entry was derived from a TLS scan",
    )

    # ── Algorithm identity ──────────────────────────────────────────────────
    algorithm_name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="Human-readable name, e.g. 'RSA-2048', 'ECDH-P256', 'ML-KEM-768'",
    )
    algorithm_oid: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="ASN.1 OID, e.g. '1.2.840.113549.1.1.1' for RSA",
    )
    category: Mapped[CryptoCategory] = mapped_column(
        Enum(CryptoCategory, name="crypto_category_enum"),
        nullable=False,
    )
    algorithm_parameters: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="{key_size, curve, padding, iv_size, tag_size, …}",
    )

    # ── PQC classification ──────────────────────────────────────────────────
    pqc_status: Mapped[PQCStatus] = mapped_column(
        Enum(PQCStatus, name="pqc_status_enum"),
        nullable=False,
        default=PQCStatus.UNKNOWN,
    )
    nist_pqc_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="NIST security level (1–5) for PQC algorithms; NULL for classical",
    )
    quantum_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="AI-computed quantum vulnerability score [0.0 – 10.0]",
    )
    cryptographic_strength_bits: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Classical security strength in bits (e.g. 112 for RSA-2048)",
    )

    # ── Usage context ────────────────────────────────────────────────────────
    usage_context: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="Where this algorithm is used: 'tls_handshake', 'jwt_signing', 'db_encryption' …",
    )
    detection_sources: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="[{tool, method, confidence, timestamp}, …]",
    )

    # ── Migration guidance ──────────────────────────────────────────────────
    replacement_algorithm: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="Recommended PQC replacement, e.g. 'ML-KEM-768 (CRYSTALS-Kyber)'",
    )
    migration_complexity: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="'low' | 'medium' | 'high' | 'critical'",
    )
    migration_recommendation: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="AI-generated migration playbook step",
    )

    # ── CycloneDX CBOM component reference ──────────────────────────────────
    cyclonedx_component: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Full CycloneDX CBOM component JSON for standards compliance",
    )

    # ── Timestamps ───────────────────────────────────────────────────────────
    first_detected: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_confirmed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────────
    asset: Mapped["MasterAsset"] = relationship(
        "MasterAsset",
        back_populates="cbom_records",
    )

    def __repr__(self) -> str:
        return (
            f"<CBOMRecord id={self.id} algorithm={self.algorithm_name!r}"
            f" pqc={self.pqc_status} asset={self.asset_id}>"
        )
