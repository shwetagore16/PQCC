"""
db/graph.py — Neo4j async driver setup and Asset Topology Graph operations.

Models the 5-tier banking network topology as a property graph:

    (Internet) -[:CONNECTS_TO]-> (LoadBalancer)
                                      |
                              [:ROUTES_TO]
                                      |
                                  (WebServer)
                                      |
                              [:CALLS]
                                      |
                                  (APIServer)
                                      |
                              [:QUERIES]
                                      |
                                  (Database)

Each node also links to its MasterAsset via the `asset_id` property.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


# ── Driver singleton ──────────────────────────────────────────────────────────

_driver: AsyncDriver | None = None


async def init_neo4j() -> None:
    """Initialise the Neo4j async driver at application startup."""
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        max_connection_lifetime=3600,
        max_connection_pool_size=50,
        connection_acquisition_timeout=30,
    )
    await _driver.verify_connectivity()
    logger.info("neo4j_connected", uri=settings.NEO4J_URI)
    await _ensure_constraints()


async def close_neo4j() -> None:
    """Close the Neo4j driver at application shutdown."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("neo4j_closed")


def get_driver() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialised. Call init_neo4j() first.")
    return _driver


@asynccontextmanager
async def get_graph_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager yielding a Neo4j async session."""
    async with get_driver().session(database="neo4j") as session:
        yield session


# FastAPI dependency version
async def graph_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_graph_session() as session:
        yield session


# ── Schema constraints & indexes ──────────────────────────────────────────────

_CONSTRAINT_QUERIES: list[str] = [
    # Uniqueness constraints (also create an implicit B-tree index)
    "CREATE CONSTRAINT asset_node_unique IF NOT EXISTS FOR (n:Asset) REQUIRE n.asset_id IS UNIQUE",
    "CREATE CONSTRAINT internet_node_unique IF NOT EXISTS FOR (n:Internet) REQUIRE n.name IS UNIQUE",
    # Node indexes for property lookups
    "CREATE INDEX asset_type_idx IF NOT EXISTS FOR (n:Asset) ON (n.asset_type)",
    "CREATE INDEX asset_host_idx IF NOT EXISTS FOR (n:Asset) ON (n.host)",
    "CREATE INDEX asset_pqc_risk_idx IF NOT EXISTS FOR (n:Asset) ON (n.pqc_risk_score)",
    "CREATE INDEX rel_latency_idx IF NOT EXISTS FOR ()-[r:CONNECTS_TO]-() ON (r.latency_ms)",
]


async def _ensure_constraints() -> None:
    """Idempotently create schema constraints and indexes."""
    async with get_graph_session() as session:
        for query in _CONSTRAINT_QUERIES:
            await session.run(query)
    logger.info("neo4j_schema_ready")


# ── Node operations ───────────────────────────────────────────────────────────

# Node label mapping (tier → Neo4j label)
TIER_LABELS: dict[str, str] = {
    "internet": "Internet",
    "load_balancer": "LoadBalancer",
    "web_server": "WebServer",
    "api_server": "APIServer",
    "database": "Database",
}

# Relationship type mapping
TIER_RELATIONSHIPS: dict[tuple[str, str], str] = {
    ("internet", "load_balancer"): "CONNECTS_TO",
    ("load_balancer", "web_server"): "ROUTES_TO",
    ("web_server", "api_server"): "CALLS",
    ("api_server", "database"): "QUERIES",
}


async def upsert_asset_node(
    session: AsyncSession,
    *,
    asset_id: uuid.UUID,
    tier: str,
    host: str,
    port: int | None = None,
    pqc_risk_score: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    MERGE an Asset node (idempotent upsert) and set its properties.

    Uses label from TIER_LABELS; falls back to generic 'Asset'.
    """
    label = TIER_LABELS.get(tier, "Asset")
    query = f"""
    MERGE (n:{label} {{asset_id: $asset_id}})
    SET
        n.host             = $host,
        n.port             = $port,
        n.tier             = $tier,
        n.pqc_risk_score   = $pqc_risk_score,
        n.metadata         = $metadata,
        n.updated_at       = datetime()
    RETURN n
    """
    await session.run(
        query,
        asset_id=str(asset_id),
        host=host,
        port=port,
        tier=tier,
        pqc_risk_score=pqc_risk_score,
        metadata=str(metadata or {}),
    )


async def upsert_topology_edge(
    session: AsyncSession,
    *,
    from_asset_id: uuid.UUID,
    to_asset_id: uuid.UUID,
    from_tier: str,
    to_tier: str,
    latency_ms: float | None = None,
    protocol: str | None = None,
) -> None:
    """
    MERGE a directed relationship between two asset nodes.

    Relationship type is derived from the tier pair.
    """
    rel_type = TIER_RELATIONSHIPS.get((from_tier, to_tier), "CONNECTED_TO")
    from_label = TIER_LABELS.get(from_tier, "Asset")
    to_label = TIER_LABELS.get(to_tier, "Asset")

    query = f"""
    MATCH (a:{from_label} {{asset_id: $from_id}})
    MATCH (b:{to_label}   {{asset_id: $to_id}})
    MERGE (a)-[r:{rel_type}]->(b)
    SET
        r.latency_ms  = $latency_ms,
        r.protocol    = $protocol,
        r.updated_at  = datetime()
    RETURN r
    """
    await session.run(
        query,
        from_id=str(from_asset_id),
        to_id=str(to_asset_id),
        latency_ms=latency_ms,
        protocol=protocol,
    )


# ── Query operations ──────────────────────────────────────────────────────────

async def get_full_topology(session: AsyncSession) -> list[dict[str, Any]]:
    """
    Return all nodes and relationships in the asset topology graph.
    Used by the dashboard to render the D3 force-directed graph.
    """
    result = await session.run(
        """
        MATCH p = (a)-[r]->(b)
        WHERE a:Internet OR a:LoadBalancer OR a:WebServer OR a:APIServer OR a:Database
        RETURN
            a.asset_id      AS from_id,
            labels(a)[0]    AS from_type,
            a.host          AS from_host,
            type(r)         AS relationship,
            b.asset_id      AS to_id,
            labels(b)[0]    AS to_type,
            b.host          AS to_host,
            r.latency_ms    AS latency_ms
        ORDER BY from_type, to_type
        """
    )
    return [dict(record) async for record in result]


async def get_attack_paths(
    session: AsyncSession,
    *,
    from_asset_id: uuid.UUID,
    max_hops: int = 5,
) -> list[dict[str, Any]]:
    """
    Find all attack paths from a given asset node using GNN-informed weights.
    Returns paths ordered by cumulative PQC risk score.
    """
    result = await session.run(
        """
        MATCH path = (start {asset_id: $start_id})-[*1..$max_hops]->(end)
        WHERE end:Database
        WITH
            path,
            [n IN nodes(path) | n.pqc_risk_score] AS scores
        WITH
            path,
            scores,
            reduce(total = 0.0, s IN scores | total + coalesce(s, 0.0)) AS total_risk
        RETURN
            [n IN nodes(path)  | {id: n.asset_id, host: n.host, tier: labels(n)[0]}] AS nodes,
            [r IN relationships(path) | type(r)]                                       AS rels,
            total_risk
        ORDER BY total_risk DESC
        LIMIT 20
        """,
        start_id=str(from_asset_id),
        max_hops=max_hops,
    )
    return [dict(record) async for record in result]


async def get_asset_neighbours(
    session: AsyncSession,
    *,
    asset_id: uuid.UUID,
    depth: int = 1,
) -> list[dict[str, Any]]:
    """Return direct (or N-hop) neighbours of an asset node."""
    result = await session.run(
        """
        MATCH (a {asset_id: $asset_id})-[r*1..$depth]-(b)
        RETURN DISTINCT
            b.asset_id      AS asset_id,
            labels(b)[0]    AS tier,
            b.host          AS host,
            b.pqc_risk_score AS pqc_risk_score
        ORDER BY b.pqc_risk_score DESC
        """,
        asset_id=str(asset_id),
        depth=depth,
    )
    return [dict(record) async for record in result]
