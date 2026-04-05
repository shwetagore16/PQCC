"""
workers/tasks/scans.py — Celery tasks for TLS inspection (Tier 2).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any

from celery import Task
from celery.utils.log import get_task_logger
from sqlalchemy import select
# Note: In a real environment, you'd import SSLyze types here.
# For this implementation, we use a robust wrapper/mock approach if sslyze is unavailable or for simplicity.

from app.core.config import get_settings
from app.db.base import AsyncSessionLocal
from app.db.models.asset import AssetStatus, MasterAsset
from app.db.models.tls_scan import TLSScanResult, TLSVersion, ScanSeverity
from app.workers.celery_app import celery_app

settings = get_settings()
logger = get_task_logger(__name__)

def _run_async(coro: Any) -> Any:
    """Execute an async coroutine from a synchronous Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)

@celery_app.task(
    name="app.workers.tasks.scans.run_tls_scan",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="scans",
    acks_late=True,
)
def run_tls_scan(self: Task, asset_id: str) -> dict[str, Any]:
    """
    Perform a deep TLS scan on a single asset.
    Simulates / Integrates with SSLyze to produce a TLSScanResult.
    """
    async def _scan() -> dict[str, Any]:
        async with AsyncSessionLocal() as db:
            asset_uuid = uuid.UUID(asset_id)
            result = await db.execute(select(MasterAsset).where(MasterAsset.id == asset_uuid))
            asset = result.scalar_one_or_none()
            
            if not asset:
                logger.error("tls_scan_asset_not_found", asset_id=asset_id)
                return {"error": "asset_not_found"}

            logger.info("tls_scan_started", host=asset.asset_value, asset_id=asset_id)
            
            # Update status to SCANNING
            asset.status = AssetStatus.SCANNING
            await db.commit()

            try:
                # ── Simulated SSLyze Logic ──────────────────────────────────────────
                # In production, this would call sslyze.Scanner()
                # Here we simulate the result for the demonstration phase.
                
                host = asset.asset_value
                port = 443
                
                # Mock result payload
                mock_raw = {
                    "sslyze_version": "6.1.0",
                    "target": f"{host}:{port}",
                    "connectivity": "successful",
                    "commands": {
                        "tls_1_2": {"is_supported": True, "ciphers": ["ECDHE-RSA-AES256-GCM-SHA384"]},
                        "tls_1_3": {"is_supported": True, "ciphers": ["TLS_AES_256_GCM_SHA384"]},
                    }
                }

                # Determine severity and PQC status
                # (Real logic would parse the cert for Kyber/Dilithium)
                supports_pqc = "kyber" in host.lower() # Simulation hack
                severity = ScanSeverity.LOW if supports_pqc else ScanSeverity.MEDIUM
                
                # ── PQC Compliance Evaluation ─────────────────────────────────────
                from .pqc_checker import PQCComplianceChecker, PQCTier
                
                # Prepare data for the checker
                eval_data = {
                    "tls_version": "TLSv1.3", # Mocked for now
                    "key_exchange": "X25519 + Kyber768 (Hybrid)" if supports_pqc else "ECDHE-RSA (Classical)",
                    "open_ports": [443, 22], # Mocked
                    "cert_expiry": mock_expiry,
                    "symmetric_key_size": 256
                }
                
                checker = PQCComplianceChecker(eval_data)
                evaluation = checker.evaluate_compliance()
                
                new_scan = TLSScanResult(
                    asset_id=asset.id,
                    host=host,
                    port=port,
                    scan_tool="sslyze",
                    scan_job_id=uuid.UUID(self.request.id) if self.request.id else uuid.uuid4(),
                    highest_tls_version=TLSVersion.TLS_1_3,
                    supports_pqc_kem=supports_pqc,
                    severity=ScanSeverity.CRITICAL if evaluation["tier"] == "Critical" else ScanSeverity.MEDIUM,
                    hndl_score=evaluation["risk_score"] / 10.0, # Scaled for score
                    cipher_suites=[
                        {"name": "TLS_AES_256_GCM_SHA384", "pqc_safe": True},
                        {"name": "ECDHE-RSA-AES256-GCM-SHA384", "pqc_safe": False}
                    ],
                    leaf_cert_expiry=mock_expiry,
                    raw_output={**mock_raw, "pqc_evaluation": evaluation},
                    scanned_at=datetime.utcnow(),
                )

                db.add(new_scan)
                
                # Update Asset attributes
                asset.status = AssetStatus.SCANNED
                asset.last_scanned = datetime.utcnow()
                asset.risk_score = new_scan.hndl_score
                
                await db.commit()
                
                from app.services.cbom_service import CBOMService
                await CBOMService.generate_from_tls_scan(db, new_scan)
                
                logger.info("tls_scan_completed", asset_id=asset_id, scan_id=str(new_scan.id))
                return {"status": "success", "scan_id": str(new_scan.id), "hndl": new_scan.hndl_score}

            except Exception as exc:
                asset.status = AssetStatus.ERROR
                await db.commit()
                logger.error("tls_scan_task_failed", asset_id=asset_id, error=str(exc))
                raise self.retry(exc=exc)

    return _run_async(_scan())
