"""
ml_engine/schemas.py — Pydantic v2 typed output schemas for all AI engine modules.

Every ML service returns one of these structured objects, making the engine
output portable: Celery tasks can serialize them as JSON, FastAPI endpoints
can return them as response models, and the dashboard can consume them directly.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Shared enums ──────────────────────────────────────────────────────────────

class PQCSafetyLevel(str, Enum):
    """NIST-aligned PQC safety classification."""
    QUANTUM_SAFE   = "quantum_safe"      # NIST PQC approved (Kyber / Dilithium / SPHINCS+ …)
    HYBRID         = "hybrid"            # Classical + PQC in tandem
    CLASSICAL      = "classical"         # Quantum-vulnerable (RSA, ECDH, DSA …)
    BROKEN         = "broken"            # Already classically broken (DES, MD5 …)


class RiskBand(str, Enum):
    CRITICAL = "critical"    # HNDL ≥ 8.0
    HIGH     = "high"        # HNDL ≥ 6.0
    MEDIUM   = "medium"      # HNDL ≥ 4.0
    LOW      = "low"         # HNDL < 4.0


# ── HNDL Scoring ─────────────────────────────────────────────────────────────

class MOSCAComponents(BaseModel):
    """Parsed MOSCA inequality components (all in years)."""
    T_harvest:  float = Field(description="Years an adversary can harvest encrypted data today")
    T_decrypt:  float = Field(description="Years a CRQC will need to break current ciphertext")
    T_migrate:  float = Field(description="Estimated years to complete PQC migration for this asset")
    mosca_risk: bool  = Field(description="True when T_harvest + T_decrypt < T_migrate (exposed)")


class HNDLScoreResult(BaseModel):
    """
    Structured HNDL risk output for one algorithm / asset combination.

    Returned by HNDLScorer.score() and stored in TLSScanResult.hndl_score.
    """
    model_config = ConfigDict(from_attributes=True)

    asset_id:      uuid.UUID | None = None
    algo:          str   = Field(description="Algorithm name, e.g. 'RSA-2048', 'ECDH-P256'")
    key_bits:      int   = Field(description="Key length in bits")
    quantum_safe:  bool  = Field(description="True if algorithm is NIST PQC approved")
    safety_level:  PQCSafetyLevel
    expiry_year:   int   = Field(description="Year this algorithm is expected to become cryptographically weak against a CRQC")
    hndl_score:    float = Field(ge=0.0, le=10.0, description="Harvest-Now-Decrypt-Later risk score")
    agility_score: float = Field(ge=0.0, le=10.0, description="Crypto-agility score (ease of migration)")
    risk_band:     RiskBand
    mosca:         MOSCAComponents
    rationale:     str   = Field(description="Human-readable explanation of the score")
    computed_at:   datetime = Field(default_factory=datetime.utcnow)


# ── GNN Attack Path ───────────────────────────────────────────────────────────

class AttackPathNode(BaseModel):
    asset_id:      str
    host:          str
    tier:          str
    pqc_risk_score: float | None


class AttackPath(BaseModel):
    """A single ranked attack path through the infrastructure graph."""
    path_id:        int
    nodes:          list[AttackPathNode]
    edge_types:     list[str]
    cvss_score:     float = Field(ge=0.0, le=10.0)
    total_risk:     float
    hop_count:      int
    entry_node:     str
    target_node:    str
    confidence:     float = Field(ge=0.0, le=1.0, description="GNN link-prediction confidence")


class AttackPathReport(BaseModel):
    """Full GNN attack-path analysis report for one scan run."""
    scan_id:         str
    source_asset_id: uuid.UUID | None
    paths:           list[AttackPath]
    top_risk_nodes:  list[AttackPathNode]
    computed_at:     datetime = Field(default_factory=datetime.utcnow)


# ── Asset Risk Clustering ─────────────────────────────────────────────────────

class ClusterProfile(BaseModel):
    """Statistical profile of one K-Means cluster."""
    cluster_id:      int
    size:            int
    centroid:        dict[str, float]   # feature_name → mean value
    dominant_algo:   str | None
    avg_hndl_score:  float
    avg_key_bits:    float
    risk_label:      str                # 'critical' | 'high' | 'medium' | 'low'


class ClusteringResult(BaseModel):
    """K-Means clustering output returned by AssetClusterer.fit_predict()."""
    optimal_k:       int
    inertia:         float
    silhouette_score: float
    cluster_profiles: list[ClusterProfile]
    asset_cluster_map: dict[str, int]   # asset_id → cluster_id
    feature_names:   list[str]
    computed_at:     datetime = Field(default_factory=datetime.utcnow)


# ── HNDL Forecasting ─────────────────────────────────────────────────────────

class ForecastBand(BaseModel):
    """P10/P50/P90 forecast values at a specific future date."""
    date:  str          # ISO-8601 date string
    p10:   float        # 10th-percentile (optimistic)
    p50:   float        # 50th-percentile (median)
    p90:   float        # 90th-percentile (pessimistic)


class MonteCarloSummary(BaseModel):
    """Summary statistics from Monte Carlo simulation."""
    n_simulations:          int
    median_exposure_year:   float   # Year 50% of CRQC arrival scenarios breach threshold
    p10_exposure_year:      float
    p90_exposure_year:      float
    prob_breach_before_2030: float  # P(breach | quantum arrival ≤ 2030)
    prob_breach_before_2035: float


class ForecastResult(BaseModel):
    """Combined Prophet + Monte Carlo HNDL exposure forecast."""
    asset_ids:        list[str]
    forecast_horizon_years: int
    prophet_forecast: list[ForecastBand]
    monte_carlo:      MonteCarloSummary
    trend_direction:  str   # 'increasing' | 'decreasing' | 'stable'
    computed_at:      datetime = Field(default_factory=datetime.utcnow)
