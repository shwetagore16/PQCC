"""
ml_engine/clustering.py — Asset Risk Clustering via Scikit-learn K-Means.

Pipeline:
  1. Extract a 12-feature risk vector per asset from the DB / HNDL scorer.
  2. Standardise features with RobustScaler (robust to HNDL score outliers).
  3. Run the Elbow Method over K ∈ [2, K_MAX] to get inertia curve.
  4. Compute Silhouette Scores for the same K range.
  5. Automatically select optimal K using a composite elbow + silhouette criterion.
  6. Fit final K-Means on that K and return ClusteringResult.

12-Feature Risk Vector:
  [0]  hndl_score           — float [0,10]
  [1]  agility_score        — float [0,10]
  [2]  key_bits_log2        — float (log2(key_bits))
  [3]  tls_version_int      — int   {0..5}
  [4]  supports_pqc_kem     — bool  {0,1}
  [5]  cert_expiry_days     — float (days to certificate expiry)
  [6]  open_ports_count     — int
  [7]  vulnerability_count  — int   (total CVEs on this asset)
  [8]  avg_cvss_score       — float [0,10]
  [9]  exposure_score       — float [0,1]
  [10] algo_risk_class      — int   {0=safe, 1=hybrid, 2=classical, 3=broken}
  [11] migration_days       — float (estimated migration duration in days)
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import structlog
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from ml_engine.schemas import ClusterProfile, ClusteringResult, RiskBand

logger = structlog.get_logger(__name__)

warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_NAMES: list[str] = [
    "hndl_score",
    "agility_score",
    "key_bits_log2",
    "tls_version_int",
    "supports_pqc_kem",
    "cert_expiry_days",
    "open_ports_count",
    "vulnerability_count",
    "avg_cvss_score",
    "exposure_score",
    "algo_risk_class",
    "migration_days",
]

K_MIN:        int = 2
K_MAX:        int = 10
KMEANS_SEED:  int = 42
KMEANS_INIT:  str = "k-means++"
N_INIT:       int = 20    # Multiple initialisations for stability
MAX_ITER:     int = 500


# ─────────────────────────────────────────────────────────────────────────────
# Feature Extractor
# ─────────────────────────────────────────────────────────────────────────────

_TLS_VERSION_INT: dict[str, int] = {
    "sslv2": 0, "sslv3": 1, "tlsv1.0": 2, "tlsv1.1": 3, "tlsv1.2": 4, "tlsv1.3": 5,
}
_ALGO_RISK_INT: dict[str, int] = {
    "quantum_safe": 0, "hybrid": 1, "classical": 2, "broken": 3,
}


def extract_feature_vector(asset: dict[str, Any]) -> list[float]:
    """
    Build a 12-element float feature vector from an asset property dict.

    Accepts dicts produced by HNDLScorer, TLSScanResult DB rows, or
    combined asset context objects — missing keys default gracefully.
    """
    key_bits  = float(asset.get("key_bits", 2048))
    key_log2  = math.log2(max(key_bits, 1.0))

    tls_ver_raw = str(asset.get("tls_version", "tlsv1.2")).lower().replace(" ", "")
    tls_ver_int = float(_TLS_VERSION_INT.get(tls_ver_raw, 4))

    algo_risk_raw = str(asset.get("algo_risk_class", "classical")).lower()
    algo_risk_int = float(_ALGO_RISK_INT.get(algo_risk_raw, 2))

    return [
        float(asset.get("hndl_score",           5.0)),
        float(asset.get("agility_score",         5.0)),
        key_log2,
        tls_ver_int,
        float(bool(asset.get("supports_pqc_kem", False))),
        float(asset.get("cert_expiry_days",      365.0)),
        float(asset.get("open_ports_count",      1.0)),
        float(asset.get("vulnerability_count",   0.0)),
        float(asset.get("avg_cvss_score",        5.0)),
        float(asset.get("exposure_score",        0.5)),
        algo_risk_int,
        float(asset.get("migration_days",        730.0)),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Optimal K Selection
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class KSelectionResult:
    """Raw scores per K used for optimal K selection."""
    k_values:          list[int]
    inertias:          list[float]
    silhouette_scores: list[float]
    optimal_k:         int
    selection_method:  str


def select_optimal_k(
    X_scaled: np.ndarray,
    k_min: int = K_MIN,
    k_max: int = K_MAX,
) -> KSelectionResult:
    """
    Automatically choose the optimal K using the composite Elbow + Silhouette method.

    Elbow Method:
        Compute inertia for each K. Find the point of maximum curvature
        (second derivative of inertia curve) — the "elbow".

    Silhouette Method:
        Compute the mean silhouette coefficient for each K.
        Maximise silhouette (higher = better-separated clusters).

    Composite:
        Normalise both scores to [0, 1] and compute:
            composite[k] = 0.4 * norm_elbow[k] + 0.6 * norm_silhouette[k]
        The K with the highest composite score is selected.

    Falls back to K=3 if the dataset is too small for meaningful clustering.
    """
    n_samples = X_scaled.shape[0]
    k_max = min(k_max, n_samples - 1, 10)
    k_vals = list(range(k_min, k_max + 1))

    if len(k_vals) < 2:
        logger.warning("insufficient_samples_for_auto_k", n=n_samples)
        return KSelectionResult(
            k_values=[k_min], inertias=[0.0], silhouette_scores=[0.0],
            optimal_k=k_min, selection_method="fallback_min_k",
        )

    inertias:   list[float] = []
    sil_scores: list[float] = []

    for k in k_vals:
        km = KMeans(
            n_clusters=k, init=KMEANS_INIT, n_init=N_INIT,
            max_iter=MAX_ITER, random_state=KMEANS_SEED,
        )
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        # Silhouette is undefined for k >= n_samples or all-same-cluster
        if len(set(labels)) > 1:
            sil_scores.append(float(silhouette_score(X_scaled, labels, sample_size=min(1000, n_samples))))
        else:
            sil_scores.append(0.0)

    # — Elbow score: second derivative of inertia (negated so higher = better elbow)
    inertia_arr = np.array(inertias)
    if len(inertia_arr) >= 3:
        d2 = np.diff(np.diff(inertia_arr))
        elbow_scores_raw = np.concatenate([[0.0, 0.0], d2])  # pad to same length
    else:
        elbow_scores_raw = np.zeros(len(k_vals))

    # Normalise elbow scores (higher second-derivative = more pronounced elbow)
    elbow_norm = _normalise(elbow_scores_raw)

    # Normalise silhouette scores
    sil_arr   = np.array(sil_scores)
    sil_norm  = _normalise(sil_arr)

    # Composite score — silhouette weighted more (proven more reliable)
    composite = 0.4 * elbow_norm + 0.6 * sil_norm
    best_idx  = int(np.argmax(composite))
    optimal_k = k_vals[best_idx]

    logger.info(
        "optimal_k_selected",
        k=optimal_k,
        silhouette=round(sil_scores[best_idx], 4),
        inertia=round(inertias[best_idx], 2),
    )

    return KSelectionResult(
        k_values=k_vals,
        inertias=inertias,
        silhouette_scores=sil_scores,
        optimal_k=optimal_k,
        selection_method="composite_elbow_silhouette",
    )


def _normalise(arr: np.ndarray) -> np.ndarray:
    """Min-max normalise to [0, 1]. Returns zeros if all values are equal."""
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-10:
        return np.zeros_like(arr, dtype=float)
    return (arr - mn) / (mx - mn)


# ─────────────────────────────────────────────────────────────────────────────
# Cluster Profiler
# ─────────────────────────────────────────────────────────────────────────────

def _risk_label_from_hndl(avg_hndl: float) -> str:
    if avg_hndl >= 7.5:
        return "critical"
    elif avg_hndl >= 5.5:
        return "high"
    elif avg_hndl >= 3.0:
        return "medium"
    return "low"


_ALGO_CLASS_MAP: dict[int, str] = {0: "quantum_safe", 1: "hybrid", 2: "classical", 3: "broken"}


def _profile_cluster(
    cluster_id:  int,
    indices:     np.ndarray,
    X_original:  np.ndarray,
    centroid:    np.ndarray,
    asset_ids:   list[str],
) -> ClusterProfile:
    """Compute summary statistics for one cluster."""
    subset      = X_original[indices]
    avg_hndl    = float(np.mean(subset[:, 0]))
    avg_key_log = float(np.mean(subset[:, 2]))
    avg_key_bits = 2 ** avg_key_log if avg_key_log > 0 else 2048.0
    dominant_algo_raw = int(round(float(np.median(subset[:, 10]))))
    dominant_algo = _ALGO_CLASS_MAP.get(dominant_algo_raw, "classical")

    centroid_dict = {name: round(float(v), 4) for name, v in zip(FEATURE_NAMES, centroid)}
    # Back-convert key_bits_log2 centroid to readable bits
    centroid_dict["key_bits_log2"] = round(2 ** centroid_dict.get("key_bits_log2", 11.0))

    return ClusterProfile(
        cluster_id=cluster_id,
        size=len(indices),
        centroid=centroid_dict,
        dominant_algo=dominant_algo,
        avg_hndl_score=round(avg_hndl, 3),
        avg_key_bits=round(avg_key_bits, 0),
        risk_label=_risk_label_from_hndl(avg_hndl),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main Clusterer Class
# ─────────────────────────────────────────────────────────────────────────────

class AssetClusterer:
    """
    Scikit-learn K-Means clustering pipeline for asset PQC risk segmentation.

    Usage::

        clusterer = AssetClusterer()
        result = clusterer.fit_predict(assets)
        print(result.optimal_k, result.silhouette_score)
    """

    def __init__(
        self,
        k_min: int = K_MIN,
        k_max: int = K_MAX,
        fixed_k: int | None = None,
    ) -> None:
        """
        Args:
            k_min:   Minimum K to consider in elbow/silhouette search.
            k_max:   Maximum K to consider (capped by data size).
            fixed_k: If set, skip auto-selection and use this K directly.
        """
        self.k_min   = k_min
        self.k_max   = k_max
        self.fixed_k = fixed_k
        self._scaler = RobustScaler()
        self._km: KMeans | None = None

    def _validate_input(self, assets: list[dict[str, Any]]) -> None:
        if len(assets) < 2:
            raise ValueError(f"Need at least 2 assets to cluster; got {len(assets)}.")

    def fit_predict(self, assets: list[dict[str, Any]]) -> ClusteringResult:
        """
        Full pipeline: extract features → scale → select K → fit → profile.

        Args:
            assets: List of asset property dicts. Each must have at least
                    the keys used by extract_feature_vector().

        Returns:
            ClusteringResult with cluster assignments and profiles.
        """
        self._validate_input(assets)

        asset_ids  = [str(a.get("asset_id", i)) for i, a in enumerate(assets)]
        X_raw      = np.array([extract_feature_vector(a) for a in assets], dtype=float)

        # Replace any NaN / inf values with column medians
        col_medians = np.nanmedian(X_raw, axis=0)
        nan_mask    = ~np.isfinite(X_raw)
        X_raw[nan_mask] = np.take(col_medians, np.where(nan_mask)[1])

        X_scaled = self._scaler.fit_transform(X_raw)

        # ── K Selection ───────────────────────────────────────────────────
        if self.fixed_k is not None:
            optimal_k  = self.fixed_k
            k_result   = None
            sil_score  = 0.0
            inertia    = 0.0
            logger.info("using_fixed_k", k=optimal_k)
        else:
            k_result  = select_optimal_k(X_scaled, self.k_min, self.k_max)
            optimal_k = k_result.optimal_k
            sil_score = k_result.silhouette_scores[k_result.k_values.index(optimal_k)]
            inertia   = k_result.inertias[k_result.k_values.index(optimal_k)]

        # ── Final K-Means fit ─────────────────────────────────────────────
        self._km = KMeans(
            n_clusters=optimal_k,
            init=KMEANS_INIT,
            n_init=N_INIT,
            max_iter=MAX_ITER,
            random_state=KMEANS_SEED,
        )
        labels    = self._km.fit_predict(X_scaled)
        centroids = self._scaler.inverse_transform(self._km.cluster_centers_)

        if self.fixed_k is not None:
            unique_labels = list(set(labels))
            if len(unique_labels) > 1:
                sil_score = float(silhouette_score(X_scaled, labels, sample_size=min(1000, len(labels))))
            inertia = float(self._km.inertia_)

        # ── Cluster Profiles ──────────────────────────────────────────────
        profiles: list[ClusterProfile] = []
        for cid in range(optimal_k):
            idxs = np.where(labels == cid)[0]
            profiles.append(
                _profile_cluster(cid, idxs, X_raw, centroids[cid], asset_ids)
            )

        # Sort profiles by avg HNDL (most critical first)
        profiles.sort(key=lambda p: p.avg_hndl_score, reverse=True)

        asset_cluster_map = {asset_ids[i]: int(labels[i]) for i in range(len(asset_ids))}

        result = ClusteringResult(
            optimal_k=optimal_k,
            inertia=round(inertia, 4),
            silhouette_score=round(sil_score, 4),
            cluster_profiles=profiles,
            asset_cluster_map=asset_cluster_map,
            feature_names=FEATURE_NAMES,
        )

        logger.info(
            "clustering_complete",
            k=optimal_k,
            silhouette=round(sil_score, 4),
            assets=len(assets),
        )
        return result

    def predict(self, assets: list[dict[str, Any]]) -> list[int]:
        """Predict cluster labels for new assets using a previously fitted model."""
        if self._km is None:
            raise RuntimeError("Call fit_predict() before predict().")
        X_raw    = np.array([extract_feature_vector(a) for a in assets], dtype=float)
        X_scaled = self._scaler.transform(X_raw)
        return list(map(int, self._km.predict(X_scaled)))
