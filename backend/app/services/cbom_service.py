"""
services/cbom_service.py — Cryptography Bill of Materials (CBOM) derivation logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.asset import MasterAsset
from app.db.models.cbom import CBOMRecord, CryptoCategory, PQCStatus
from app.db.models.tls_scan import TLSScanResult, TLSVersion

class CBOMService:
    """
    Service for generating and managing CBOM records.
    Derives algorithm-level inventory from scanner outputs (SSLyze, etc.).
    """

    @staticmethod
    async def generate_from_tls_scan(
        db: AsyncSession,
        scan_result: TLSScanResult,
    ) -> list[CBOMRecord]:
        """
        Derive CBOM records (Algorithm, Key Exchange, Cipher) from a TLS scan result.
        """
        new_records: list[CBOMRecord] = []
        
        # 1. Protocol Version
        if scan_result.highest_tls_version:
            proto_record = CBOMRecord(
                asset_id=scan_result.asset_id,
                scan_result_id=scan_result.id,
                algorithm_name=scan_result.highest_tls_version.value,
                category=CryptoCategory.PROTOCOL,
                pqc_status=PQCStatus.CLASSICAL if scan_result.highest_tls_version.value != "TLSv1.3" else PQCStatus.HYBRID,
                usage_context="tls_handshake_protocol",
                detection_sources=[{"tool": "sslyze", "method": "protocol_discovery"}]
            )
            new_records.append(proto_record)

        # 2. Cipher Suites (derive symmetric and key exchange)
        if scan_result.cipher_suites:
            for suite in scan_result.cipher_suites:
                suite_name = suite.get("name", "Unknown")
                pqc_safe = suite.get("pqc_safe", False)
                
                # Logic to break down suite name into primitives would go here
                # Mocking a Cipher record
                cipher_record = CBOMRecord(
                    asset_id=scan_result.asset_id,
                    scan_result_id=scan_result.id,
                    algorithm_name=suite_name,
                    category=CryptoCategory.SYMMETRIC_CIPHER,
                    pqc_status=PQCStatus.SAFE if pqc_safe else PQCStatus.CLASSICAL,
                    usage_context="tls_cipher_suite",
                    detection_sources=[{"tool": "sslyze", "method": "handshake_negotiation"}]
                )
                new_records.append(cipher_record)

        # Bulk add
        for rec in new_records:
            db.add(rec)
        
        await db.commit()
        return new_records

    @staticmethod
    async def get_cbom_for_asset(
        db: AsyncSession,
        asset_id: uuid.UUID
    ) -> list[CBOMRecord]:
        """Retrieve the current CBOM for an asset."""
        result = await db.execute(select(CBOMRecord).where(CBOMRecord.asset_id == asset_id))
        return list(result.scalars().all())
