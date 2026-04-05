"""
api/v1/endpoints/topology.py — Network Topology and Attack Path API endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import AsyncSession as GraphSession

from app.db.graph import get_full_topology, get_attack_paths, graph_session

router = APIRouter(prefix="/topology", tags=["Topology"])

@router.get("/", response_model=list[dict[str, Any]])
async def get_topology_graph(
    session: GraphSession = Depends(graph_session),
) -> list[dict[str, Any]]:
    """
    Retrieve the full network topology graph from Neo4j.
    Used for D3.js visualization on the dashboard.
    """
    try:
        topology = await get_full_topology(session)
        return topology
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j query failed: {str(e)}")

@router.get("/attack-paths/{asset_id}", response_model=list[dict[str, Any]])
async def get_asset_attack_paths(
    asset_id: uuid.UUID,
    max_hops: int = Query(5, ge=1, le=10),
    session: GraphSession = Depends(graph_session),
) -> list[dict[str, Any]]:
    """
    Compute potential attack paths from the specified asset to sensitive targets (Databases).
    """
    try:
        paths = await get_attack_paths(session, from_asset_id=asset_id, max_hops=max_hops)
        return paths
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attack path computation failed: {str(e)}")
