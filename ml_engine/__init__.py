"""
ml_engine/__init__.py — Public package API for the AI Intelligence Engine.

Exposes the four primary service classes and the shared schema types
so downstream Celery tasks and FastAPI endpoints can import cleanly::

    from ml_engine import HNDLScorer, AttackPathSimulator, AssetClusterer, HNDLForecastingService
"""

from __future__ import annotations

from ml_engine.clustering import AssetClusterer
from ml_engine.forecasting import HNDLForecastingService, MonteCarloCRQCSimulator, HNDLProphetForecaster
from ml_engine.gnn_attack_path import AttackPathGNN, AttackPathSimulator
from ml_engine.hndl_scorer import HNDLScorer, ALGO_CATALOGUE
from ml_engine.schemas import (
    AttackPath,
    AttackPathNode,
    AttackPathReport,
    ClusteringResult,
    ClusterProfile,
    ForecastBand,
    ForecastResult,
    HNDLScoreResult,
    MOSCAComponents,
    MonteCarloSummary,
    PQCSafetyLevel,
    RiskBand,
)

__all__: list[str] = [
    # Services
    "HNDLScorer",
    "AttackPathGNN",
    "AttackPathSimulator",
    "AssetClusterer",
    "HNDLForecastingService",
    "HNDLProphetForecaster",
    "MonteCarloCRQCSimulator",
    # Data
    "ALGO_CATALOGUE",
    # Schemas
    "HNDLScoreResult",
    "MOSCAComponents",
    "PQCSafetyLevel",
    "RiskBand",
    "AttackPath",
    "AttackPathNode",
    "AttackPathReport",
    "ClusteringResult",
    "ClusterProfile",
    "ForecastBand",
    "ForecastResult",
    "MonteCarloSummary",
]

__version__: str = "0.3.0"
