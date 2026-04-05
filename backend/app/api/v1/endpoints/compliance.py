"""
api/v1/endpoints/compliance.py — FastAPI Compliance Engine REST + WebSocket API.

REST Endpoints:
  POST /compliance/label          — Label a single asset
  POST /compliance/label/batch    — Label multiple assets
  GET  /compliance/playbook/{id}  — Retrieve a generated playbook
  POST /compliance/playbook/generate — Generate playbooks from a label result
  POST /compliance/playbook/{id}/execute  — Trigger execution (requires approval)
  POST /compliance/approval/{id}/request  — Request human approval for critical playbook
  GET  /compliance/approval/{id}  — Poll approval status

WebSocket:
  WS  /compliance/ws/alerts       — Streaming TLS anomaly alerts (JA3/JARM)
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import Annotated, Any

import structlog
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.compliance.approval_gate import ApprovalGate, ApprovalRecord
from app.compliance.labeling import ComplianceLabelResult, PQCComplianceLabeler
from app.compliance.playbooks import RemediationPlaybook, RemediationPlaybookGenerator
from app.core.logging import logger
from app.db.base import get_db

router = APIRouter(prefix="/compliance", tags=["Compliance Engine"])

# ── Service singletons ────────────────────────────────────────────────────────
_labeler   = PQCComplianceLabeler()
_generator = RemediationPlaybookGenerator()
_gate      = ApprovalGate()

# In-memory store for this phase (replace with DB/Redis in production)
_playbook_store:  dict[str, RemediationPlaybook]  = {}
_approval_store:  dict[str, ApprovalRecord]        = {}


# ─────────────────────────────────────────────────────────────────────────────
# REST — Labeling
# ─────────────────────────────────────────────────────────────────────────────

class LabelRequest(BaseModel):
    algorithms: list[str | dict[str, Any]] = Field(
        ...,
        description="List of algorithm names or {algo, key_bits} dicts",
        examples=[["rsa-2048", "ecdh-p256", {"algo": "aes-256-gcm", "key_bits": 256}]],
    )
    asset_id:   uuid.UUID | None = None
    host:       str | None       = None


class BatchLabelRequest(BaseModel):
    assets: list[LabelRequest]


@router.post(
    "/label",
    response_model=ComplianceLabelResult,
    summary="Label a single asset with its PQC compliance status",
)
async def label_asset(payload: LabelRequest) -> ComplianceLabelResult:
    result = _labeler.label_asset(
        algorithms=payload.algorithms,
        asset_id=payload.asset_id,
        host=payload.host,
    )
    return result


@router.post(
    "/label/batch",
    response_model=list[ComplianceLabelResult],
    summary="Label multiple assets in one request",
)
async def label_batch(payload: BatchLabelRequest) -> list[ComplianceLabelResult]:
    return _labeler.label_batch(
        [
            {
                "algorithms": a.algorithms,
                "asset_id":   a.asset_id,
                "host":       a.host,
            }
            for a in payload.assets
        ]
    )


# ─────────────────────────────────────────────────────────────────────────────
# REST — Playbooks
# ─────────────────────────────────────────────────────────────────────────────

class GeneratePlaybookRequest(BaseModel):
    label_result: ComplianceLabelResult


@router.post(
    "/playbook/generate",
    response_model=list[RemediationPlaybook],
    status_code=status.HTTP_201_CREATED,
    summary="Generate Ansible remediation playbooks from a compliance label",
)
async def generate_playbooks(payload: GeneratePlaybookRequest) -> list[RemediationPlaybook]:
    playbooks = _generator.generate(payload.label_result)
    for pb in playbooks:
        _playbook_store[pb.playbook_id] = pb
    return playbooks


@router.get(
    "/playbook/{playbook_id}",
    response_model=RemediationPlaybook,
    summary="Retrieve a generated playbook by ID",
)
async def get_playbook(playbook_id: str) -> RemediationPlaybook:
    pb = _playbook_store.get(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found.")
    return pb


@router.get(
    "/playbook/{playbook_id}/yaml",
    response_class=__import__("fastapi").responses.PlainTextResponse,
    summary="Download the Ansible YAML for a playbook",
)
async def get_playbook_yaml(playbook_id: str) -> str:
    pb = _playbook_store.get(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found.")
    return pb.to_ansible_yaml()


# ─────────────────────────────────────────────────────────────────────────────
# REST — Approval Gate
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/approval/{playbook_id}/request",
    response_model=ApprovalRecord,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request human approval for a critical-tier playbook",
)
async def request_approval(playbook_id: str) -> ApprovalRecord:
    pb = _playbook_store.get(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found.")
    if pb.tier.value != "critical":
        raise HTTPException(
            status_code=400,
            detail="Approval gate only required for CRITICAL-tier playbooks.",
        )

    record = await _gate.request_approval(
        playbook_id=playbook_id,
        asset_id=str(pb.asset_id) if pb.asset_id else None,
        host=pb.host or "unknown",
        tier=pb.tier.value,
        description=pb.description,
    )
    _approval_store[record.approval_id] = record
    pb.approval_ticket = record.ticket_id
    return record


@router.get(
    "/approval/{approval_id}",
    response_model=ApprovalRecord,
    summary="Poll the current approval status",
)
async def get_approval(approval_id: str) -> ApprovalRecord:
    record = _approval_store.get(approval_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found.")
    updated = await _gate.check_approval(record)
    _approval_store[approval_id] = updated
    return updated


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket — TLS Anomaly Alert Stream
# ─────────────────────────────────────────────────────────────────────────────

class AlertConnectionManager:
    """Manages connected WebSocket SOC analyst clients."""

    def __init__(self) -> None:
        self._active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._active.append(ws)
        logger.info("ws_client_connected", total=len(self._active))

    def disconnect(self, ws: WebSocket) -> None:
        self._active.remove(ws)
        logger.info("ws_client_disconnected", total=len(self._active))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Fan-out an alert to all connected SOC analysts."""
        dead: list[WebSocket] = []
        for ws in self._active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._active.remove(ws)


_manager = AlertConnectionManager()


@router.websocket("/ws/alerts")
async def tls_alert_stream(ws: WebSocket) -> None:
    """
    WebSocket endpoint for real-time TLS anomaly alerts.

    Each message is a JSON object:
    {
      "type":        "tls_anomaly",
      "asset_id":   "<uuid>",
      "host":        "api.pnb.co.in",
      "alert_type":  "ja3_fingerprint_mismatch" | "jarm_change" | "new_cipher_suite",
      "ja3":         "<32-char hex>",
      "jarm":        "<62-char hex>",
      "severity":    "critical" | "high" | "medium",
      "details":     {...},
      "timestamp":   "<ISO-8601>"
    }

    The server sends a synthetic keep-alive every 30 seconds.
    """
    await _manager.connect(ws)
    try:
        while True:
            # Keep-alive heartbeat — client can send "ping" messages
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                msg  = json.loads(data)
                if msg.get("type") == "ping":
                    await ws.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            except asyncio.TimeoutError:
                # Send keep-alive
                await ws.send_json({
                    "type":      "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_clients": len(_manager._active),
                })
    except WebSocketDisconnect:
        _manager.disconnect(ws)


async def broadcast_tls_alert(alert: dict[str, Any]) -> None:
    """
    External entry point: Scanner/AI tasks call this to push alerts to SOC.
    Called from Celery tasks or SSLyze scan completion handlers.
    """
    await _manager.broadcast(alert)
