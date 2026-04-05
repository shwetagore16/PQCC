"""
workers/tasks/discovery.py — Celery tasks for Asset Discovery (Tier 1).

Tasks:
  - run_amass_discovery  : subprocess Amass for subdomain enumeration
  - run_shodan_query     : Shodan Internet DB query via shodanpy
  - refresh_all_assets   : beat-scheduled batch refresh
  - ingest_seed_domain   : lightweight DB insertion task
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import uuid
from typing import Any

import shodan
from celery import Task
from celery.utils.log import get_task_logger
from sqlalchemy import select

from app.core.config import get_settings
from app.db.base import AsyncSessionLocal
from app.db.models.asset import AssetStatus, AssetType, MasterAsset
from app.workers.celery_app import celery_app

settings = get_settings()
logger = get_task_logger(__name__)


# ── Helper: run async code inside a Celery (sync) task ───────────────────────

def _run_async(coro: Any) -> Any:
    """Execute an async coroutine from a synchronous Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Task: ingest a seed domain ───────────────────────────────────────────────

@celery_app.task(
    name="app.workers.tasks.discovery.ingest_seed_domain",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="discovery",
    acks_late=True,
)
def ingest_seed_domain(
    self: Task,
    domain: str,
    organization: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    Persist a seed domain as a PENDING MasterAsset row.
    Idempotent — will skip if the domain already exists.
    """
    async def _upsert() -> dict[str, Any]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(MasterAsset).where(
                    MasterAsset.asset_value == domain,
                    MasterAsset.asset_type == AssetType.DOMAIN,
                )
            )
            asset = result.scalar_one_or_none()

            if asset is None:
                asset = MasterAsset(
                    asset_type=AssetType.DOMAIN,
                    asset_value=domain,
                    organization=organization,
                    seed_domain=domain,
                    status=AssetStatus.PENDING,
                    tags=tags or [],
                )
                db.add(asset)
                await db.commit()
                await db.refresh(asset)
                logger.info("seed_domain_ingested", domain=domain, asset_id=str(asset.id))
                return {"asset_id": str(asset.id), "created": True}

            logger.info("seed_domain_exists", domain=domain, asset_id=str(asset.id))
            return {"asset_id": str(asset.id), "created": False}

    try:
        return _run_async(_upsert())
    except Exception as exc:
        logger.error("ingest_seed_domain_failed", domain=domain, error=str(exc))
        raise self.retry(exc=exc)


# ── Task: Amass subdomain enumeration ────────────────────────────────────────

@celery_app.task(
    name="app.workers.tasks.discovery.run_amass_discovery",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    time_limit=600,          # 10-minute hard limit
    soft_time_limit=540,
    queue="discovery",
    acks_late=True,
    rate_limit="10/m",
)
def run_amass_discovery(
    self: Task,
    seed_domain: str,
    organization: str | None = None,
) -> dict[str, Any]:
    """
    Run Amass passive enumeration against a seed domain and persist discovered
    subdomains as MasterAsset rows.

    Returns a summary dict with counts.
    """
    logger.info("amass_started", domain=seed_domain)

    try:
        proc = subprocess.run(
            [
                "amass", "enum",
                "-passive",
                "-d", seed_domain,
                "-json", "-",
                "-timeout", "8",      # minutes
            ],
            capture_output=True,
            text=True,
            timeout=settings.SCAN_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        logger.warning("amass_not_found", domain=seed_domain)
        return {"domain": seed_domain, "discovered": 0, "error": "amass not installed"}
    except subprocess.TimeoutExpired as exc:
        raise self.retry(exc=exc)

    discovered_domains: list[str] = []
    for line in proc.stdout.splitlines():
        try:
            record = json.loads(line)
            if name := record.get("name"):
                discovered_domains.append(name)
        except json.JSONDecodeError:
            continue

    async def _persist() -> int:
        count = 0
        async with AsyncSessionLocal() as db:
            for fqdn in set(discovered_domains):
                existing = await db.execute(
                    select(MasterAsset).where(
                        MasterAsset.asset_value == fqdn,
                        MasterAsset.asset_type == AssetType.DOMAIN,
                    )
                )
                if existing.scalar_one_or_none() is None:
                    db.add(
                        MasterAsset(
                            asset_type=AssetType.DOMAIN,
                            asset_value=fqdn,
                            organization=organization,
                            seed_domain=seed_domain,
                            status=AssetStatus.PENDING,
                            metadata_={"discovery_source": "amass"},
                        )
                    )
                    count += 1
            await db.commit()
        return count

    persisted = _run_async(_persist())
    logger.info("amass_complete", domain=seed_domain, discovered=len(discovered_domains), persisted=persisted)
    return {
        "domain": seed_domain,
        "discovered": len(discovered_domains),
        "persisted": persisted,
    }


# ── Task: Shodan Internet DB query ────────────────────────────────────────────

@celery_app.task(
    name="app.workers.tasks.discovery.run_shodan_query",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    time_limit=120,
    queue="discovery",
    acks_late=True,
    rate_limit="5/m",       # Shodan rate limit: 1 query/second on free tier
)
def run_shodan_query(
    self: Task,
    seed_domain: str,
    organization: str | None = None,
) -> dict[str, Any]:
    """
    Query Shodan for hosts associated with the seed domain's SSL certificates
    and persist discovered IPs as MasterAsset rows.
    """
    if not settings.SHODAN_API_KEY:
        logger.warning("shodan_no_api_key")
        return {"domain": seed_domain, "discovered": 0, "error": "No Shodan API key configured"}

    try:
        api = shodan.Shodan(settings.SHODAN_API_KEY)
        results = api.search(f"ssl.cert.subject.cn:{seed_domain}", page=1)
        hosts = results.get("matches", [])
    except shodan.APIError as exc:
        raise self.retry(exc=exc)

    async def _persist() -> int:
        count = 0
        async with AsyncSessionLocal() as db:
            for host in hosts:
                ip = host.get("ip_str")
                if not ip:
                    continue
                existing = await db.execute(
                    select(MasterAsset).where(
                        MasterAsset.asset_value == ip,
                        MasterAsset.asset_type == AssetType.IP_ADDRESS,
                    )
                )
                if existing.scalar_one_or_none() is None:
                    db.add(
                        MasterAsset(
                            asset_type=AssetType.IP_ADDRESS,
                            asset_value=ip,
                            organization=organization,
                            seed_domain=seed_domain,
                            status=AssetStatus.PENDING,
                            metadata_={
                                "discovery_source": "shodan",
                                "ports": host.get("ports", []),
                                "org": host.get("org"),
                                "isp": host.get("isp"),
                                "country": host.get("location", {}).get("country_name"),
                            },
                        )
                    )
                    count += 1
            await db.commit()
        return count

    persisted = _run_async(_persist())
    logger.info("shodan_complete", domain=seed_domain, total=len(hosts), persisted=persisted)
    return {"domain": seed_domain, "discovered": len(hosts), "persisted": persisted}


# ── Beat task: daily refresh ─────────────────────────────────────────────────

@celery_app.task(
    name="app.workers.tasks.discovery.refresh_all_assets",
    queue="discovery",
)
def refresh_all_assets() -> dict[str, Any]:
    """
    Daily beat task: re-discover all seed domains currently tracked in the DB.
    """
    async def _get_seeds() -> list[str]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(MasterAsset.asset_value).where(
                    MasterAsset.asset_type == AssetType.DOMAIN,
                    MasterAsset.seed_domain == MasterAsset.asset_value,
                )
            )
            return [row[0] for row in result.fetchall()]

    seeds = _run_async(_get_seeds())
    for domain in seeds:
        run_amass_discovery.apply_async(args=[domain], queue="discovery")
        run_shodan_query.apply_async(args=[domain], queue="discovery")

    logger.info("refresh_all_assets_dispatched", count=len(seeds))
    return {"dispatched": len(seeds)}
