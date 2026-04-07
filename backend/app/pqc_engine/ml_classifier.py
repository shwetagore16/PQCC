"""Lightweight ML-style classifier for PQC readiness."""

from __future__ import annotations

import math
from typing import Any


def _normalise(value: Any) -> str:
    return str(value or "").strip().lower()


def _parse_key_size(value: Any) -> int | None:
    raw = _normalise(value)
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def _build_features(properties: dict[str, Any]) -> dict[str, float]:
    tls = _normalise(properties.get("tls_version"))
    combined = " ".join(_normalise(properties.get(k)) for k in (
        "cipher",
        "key_exchange",
        "signature_algorithm",
        "certificate_algorithm",
    ))

    key_size = _parse_key_size(properties.get("key_size"))

    features = {
        "tls_legacy": 1.0 if ("1.0" in tls or "1.1" in tls) else 0.0,
        "tls12": 1.0 if "1.2" in tls else 0.0,
        "rsa_present": 1.0 if "rsa" in combined else 0.0,
        "sha1_present": 1.0 if "sha1" in combined else 0.0,
        "key_size_small": 1.0 if (key_size is not None and key_size <= 2048) else 0.0,
        "has_pqc": 1.0 if any(token in combined for token in (
            "ml-kem",
            "kyber",
            "dilithium",
            "falcon",
            "sphincs",
            "ml-dsa",
        )) else 0.0,
        "has_hybrid": 1.0 if "hybrid" in combined else 0.0,
    }

    return features


def predict_pqc_ready(properties: dict[str, Any]) -> dict[str, Any]:
    """Return a PQC readiness label and confidence using a simple model."""
    features = _build_features(properties)

    weights = {
        "bias": -0.2,
        "tls_legacy": 1.5,
        "tls12": 0.6,
        "rsa_present": 0.7,
        "sha1_present": 1.0,
        "key_size_small": 0.8,
        "has_pqc": -1.5,
        "has_hybrid": -0.8,
    }

    z = weights["bias"]
    for name, value in features.items():
        z += weights.get(name, 0.0) * value

    prob_not_ready = 1 / (1 + math.exp(-z))
    label = "NOT_READY" if prob_not_ready >= 0.5 else "PQC_READY"
    confidence = round(max(prob_not_ready, 1 - prob_not_ready), 2)

    return {
        "label": label,
        "confidence": confidence,
        "prob_not_ready": round(prob_not_ready, 2),
        "features": features,
    }
