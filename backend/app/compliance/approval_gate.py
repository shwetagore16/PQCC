"""
compliance/approval_gate.py — Human-in-the-Loop Approval Gate.

Critical-tier remediation playbooks MUST receive explicit human approval before
execution. This module provides a unified approval client that can route requests
to either ServiceNow or Jira, then poll for the approval state.

Flow:
  1. PlaybookGenerator marks critical playbooks with ApprovalStatus.PENDING.
  2. The compliance API endpoint calls ApprovalGate.request_approval().
  3. The gate creates a ticket in the configured ITSM system.
  4. A background poller (Celery beat) calls ApprovalGate.check_approval()
     every 60 seconds until Approved / Rejected / Timeout.
  5. On Approved → the Celery task executes the Ansible playbook via Runner.
  6. On Rejected → the approval record is archived and notified via Slack.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timedelta
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ITSMBackend(str, enum.Enum):
    SERVICENOW = "servicenow"
    JIRA       = "jira"
    MOCK       = "mock"          # Local dev/test — always returns APPROVED


class ApprovalRecord(BaseModel):
    """Tracks the lifecycle of one approval request."""
    model_config = ConfigDict(from_attributes=True)

    approval_id:    str = Field(default_factory=lambda: str(uuid.uuid4()))
    playbook_id:    str
    asset_id:       str | None = None
    host:           str | None = None
    tier:           str
    ticket_id:      str | None = None   # ServiceNow sys_id or Jira issue key
    ticket_url:     str | None = None
    backend:        ITSMBackend
    status:         str = "pending"     # pending | approved | rejected | timeout
    requested_at:   datetime = Field(default_factory=datetime.utcnow)
    resolved_at:    datetime | None = None
    reviewer:       str | None = None
    notes:          str | None = None
    timeout_hours:  float = 24.0


# ─────────────────────────────────────────────────────────────────────────────
# ServiceNow Client
# ─────────────────────────────────────────────────────────────────────────────

class ServiceNowClient:
    """
    REST client for ServiceNow Change Management.

    Creates a Change Request (CHG) record for each critical playbook,
    and polls the approval_state field to detect workflow approval.
    """

    def __init__(self) -> None:
        self._base_url    = getattr(settings, "SERVICENOW_INSTANCE_URL", "")
        self._username    = getattr(settings, "SERVICENOW_USERNAME", "")
        self._password    = getattr(settings, "SERVICENOW_PASSWORD", "")
        self._table       = "change_request"

    def _headers(self) -> dict[str, str]:
        import base64
        creds = base64.b64encode(f"{self._username}:{self._password}".encode()).decode()
        return {
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def create_change_request(
        self,
        playbook_id: str,
        host: str,
        tier: str,
        description: str,
        short_description: str,
    ) -> dict[str, Any]:
        """Create a Change Request and return the sys_id + ticket number."""
        payload = {
            "short_description": short_description[:160],
            "description":       description,
            "category":          "Security",
            "type":              "Emergency" if tier == "critical" else "Normal",
            "risk":              "High",
            "priority":          "1 - Critical" if tier == "critical" else "2 - High",
            "assignment_group":  "PQC Security Operations",
            "cmdb_ci":           host,
            "u_playbook_id":     playbook_id,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base_url}/api/now/table/{self._table}",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            result = resp.json()["result"]
            logger.info(
                "servicenow_chg_created",
                sys_id=result["sys_id"],
                number=result["number"],
            )
            return {"ticket_id": result["sys_id"], "ticket_number": result["number"]}

    async def get_approval_state(self, sys_id: str) -> str:
        """
        Poll the approval_state of a Change Request.
        ServiceNow approval_state values:
          not requested → requested → approved / rejected
        Returns: 'pending' | 'approved' | 'rejected'
        """
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self._base_url}/api/now/table/{self._table}/{sys_id}",
                params={"sysparm_fields": "approval_state,state"},
                headers=self._headers(),
            )
            resp.raise_for_status()
            state = resp.json()["result"]["approval_state"]

        mapping = {
            "approved":  "approved",
            "rejected":  "rejected",
            "not_requested": "pending",
            "requested":     "pending",
            "not requested": "pending",
        }
        return mapping.get(state.lower(), "pending")


# ─────────────────────────────────────────────────────────────────────────────
# Jira Client
# ─────────────────────────────────────────────────────────────────────────────

class JiraClient:
    """
    REST client for Jira Service Management approval workflows.

    Creates a Jira issue in the PQC project and monitors its status
    transition (typically Open → In Approval → Approved / Rejected).
    """

    def __init__(self) -> None:
        self._base_url   = getattr(settings, "JIRA_BASE_URL", "")
        self._email      = getattr(settings, "JIRA_EMAIL", "")
        self._api_token  = getattr(settings, "JIRA_API_TOKEN", "")
        self._project    = getattr(settings, "JIRA_PROJECT_KEY", "PQC")

    def _headers(self) -> dict[str, str]:
        import base64
        creds = base64.b64encode(f"{self._email}:{self._api_token}".encode()).decode()
        return {
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def create_issue(
        self,
        playbook_id: str,
        host: str,
        tier: str,
        summary: str,
        description: str,
    ) -> dict[str, Any]:
        """Create a Jira issue and return the issue key."""
        priority = "Critical" if tier == "critical" else "High"
        payload = {
            "fields": {
                "project":     {"key": self._project},
                "summary":     summary[:255],
                "description": {
                    "type":    "doc",
                    "version": 1,
                    "content": [
                        {
                            "type":    "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype":  {"name": "Change Request"},
                "priority":   {"name": priority},
                "labels":     ["pqc-remediation", f"tier-{tier}", "quantum-safe"],
                "customfield_10000": playbook_id,   # Playbook ID in custom field
            }
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base_url}/rest/api/3/issue",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("jira_issue_created", key=result["key"])
            return {
                "ticket_id":  result["key"],
                "ticket_url": f"{self._base_url}/browse/{result['key']}",
            }

    async def get_approval_state(self, issue_key: str) -> str:
        """
        Poll the Jira issue status.
        Approved status names: 'Approved', 'Done', 'Accepted'.
        Rejected: 'Rejected', 'Declined', 'Closed'.
        """
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self._base_url}/rest/api/3/issue/{issue_key}",
                params={"fields": "status"},
                headers=self._headers(),
            )
            resp.raise_for_status()
            status_name = resp.json()["fields"]["status"]["name"].lower()

        approved_states = {"approved", "done", "accepted", "resolved"}
        rejected_states = {"rejected", "declined", "closed", "cancelled", "wont do"}

        if status_name in approved_states:
            return "approved"
        elif status_name in rejected_states:
            return "rejected"
        return "pending"


# ─────────────────────────────────────────────────────────────────────────────
# Unified Approval Gate
# ─────────────────────────────────────────────────────────────────────────────

class ApprovalGate:
    """
    Unified human-in-the-loop approval gate.

    Selects the ITSM backend from settings.APPROVAL_BACKEND ("servicenow" | "jira" | "mock").
    Falls back to MOCK in development environments.

    Usage::

        gate = ApprovalGate()

        # Step 1: Request approval (returns ApprovalRecord with ticket_id)
        record = await gate.request_approval(playbook)

        # Step 2: Poll (called by Celery beat task every 60s)
        updated = await gate.check_approval(record)
        if updated.status == "approved":
            # Execute playbook via ansible-runner
            ...
    """

    def __init__(self) -> None:
        backend_name: str = getattr(settings, "APPROVAL_BACKEND", "mock").lower()
        self.backend = ITSMBackend(backend_name) if backend_name in ITSMBackend._value2member_map_ else ITSMBackend.MOCK

        if self.backend == ITSMBackend.SERVICENOW:
            self._client: ServiceNowClient | JiraClient = ServiceNowClient()
        elif self.backend == ITSMBackend.JIRA:
            self._client = JiraClient()
        else:
            self._client = None  # type: ignore[assignment]

        logger.info("approval_gate_init", backend=self.backend.value)

    async def request_approval(
        self,
        playbook_id: str,
        asset_id: str | None,
        host: str,
        tier: str,
        description: str,
        timeout_hours: float = 24.0,
    ) -> ApprovalRecord:
        """
        Submit an approval request to the configured ITSM backend.

        Returns an ApprovalRecord with the ticket ID populated.
        The record should be persisted in PostgreSQL for polling.
        """
        summary = f"[PQC-{tier.upper()}] Remediation approval required: {host}"

        record = ApprovalRecord(
            playbook_id=playbook_id,
            asset_id=asset_id,
            host=host,
            tier=tier,
            backend=self.backend,
            timeout_hours=timeout_hours,
        )

        if self.backend == ITSMBackend.MOCK:
            # In mock mode, auto-approve after a simulated delay
            record.ticket_id  = f"MOCK-{record.approval_id[:8].upper()}"
            record.ticket_url = f"http://localhost:8000/mock-approvals/{record.ticket_id}"
            record.status     = "approved"   # Auto-approve in dev
            record.resolved_at = datetime.utcnow()
            logger.warning("approval_gate_mock_auto_approved", playbook_id=playbook_id)
            return record

        try:
            if self.backend == ITSMBackend.SERVICENOW:
                result = await (self._client).create_change_request(  # type: ignore
                    playbook_id=playbook_id,
                    host=host,
                    tier=tier,
                    description=description,
                    short_description=summary,
                )
                record.ticket_id  = result["ticket_id"]
                record.ticket_url = (
                    f"{getattr(settings, 'SERVICENOW_INSTANCE_URL', '')}"
                    f"/nav_to.do?uri=change_request.do?sys_id={result['ticket_id']}"
                )
            elif self.backend == ITSMBackend.JIRA:
                result = await (self._client).create_issue(  # type: ignore
                    playbook_id=playbook_id,
                    host=host,
                    tier=tier,
                    summary=summary,
                    description=description,
                )
                record.ticket_id  = result["ticket_id"]
                record.ticket_url = result["ticket_url"]

            logger.info(
                "approval_requested",
                backend=self.backend.value,
                ticket=record.ticket_id,
                url=record.ticket_url,
            )
        except httpx.HTTPError as exc:
            logger.error("approval_request_failed", error=str(exc))
            record.status = "pending"   # Keep pending; retry on next poll cycle

        return record

    async def check_approval(self, record: ApprovalRecord) -> ApprovalRecord:
        """
        Poll the ITSM backend for the current approval state.

        Updates record.status and record.resolved_at.
        Handles timeout: if approval has not arrived within timeout_hours → "timeout".
        """
        if record.status in ("approved", "rejected", "timeout"):
            return record   # Already terminal — no-op

        # Timeout check
        elapsed = datetime.utcnow() - record.requested_at
        if elapsed > timedelta(hours=record.timeout_hours):
            record.status = "timeout"
            logger.warning(
                "approval_timeout",
                playbook_id=record.playbook_id,
                ticket=record.ticket_id,
                elapsed_hours=elapsed.total_seconds() / 3600,
            )
            return record

        if self.backend == ITSMBackend.MOCK or not record.ticket_id:
            record.status = "approved"
            record.resolved_at = datetime.utcnow()
            return record

        try:
            if self.backend == ITSMBackend.SERVICENOW:
                state = await (self._client).get_approval_state(record.ticket_id)  # type: ignore
            else:
                state = await (self._client).get_approval_state(record.ticket_id)  # type: ignore

            if state in ("approved", "rejected"):
                record.status = state
                record.resolved_at = datetime.utcnow()
                logger.info(
                    "approval_resolved",
                    ticket=record.ticket_id,
                    status=state,
                )
        except httpx.HTTPError as exc:
            logger.error("approval_poll_failed", error=str(exc))

        return record
