"""Policy engine for PQC historical and future risk rules."""

from __future__ import annotations

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


def evaluate_policy(properties: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate policy rules and return a future risk score and drivers."""
    drivers: list[str] = []
    score = 0

    tls = _normalise(properties.get("tls_version"))
    if "1.0" in tls or "1.1" in tls:
        score += 40
        drivers.append("TLS 1.0/1.1 deprecated")
    elif "1.2" in tls:
        score += 20
        drivers.append("TLS 1.2 nearing deprecation")

    combined = " ".join(_normalise(properties.get(k)) for k in (
        "cipher",
        "key_exchange",
        "signature_algorithm",
        "certificate_algorithm",
    ))

    key_size = _parse_key_size(properties.get("key_size"))
    if "rsa" in combined and key_size is not None and key_size < 2048:
        score += 30
        drivers.append("RSA key size < 2048")
    elif "rsa" in combined and key_size is not None and key_size <= 2048:
        score += 20
        drivers.append("RSA key size 2048")

    if "sha1" in combined:
        score += 40
        drivers.append("SHA1 usage detected")

    has_pqc = any(token in combined for token in (
        "ml-kem",
        "kyber",
        "dilithium",
        "falcon",
        "sphincs",
        "ml-dsa",
    ))
    has_hybrid = "hybrid" in combined

    if has_pqc:
        score -= 15
        drivers.append("PQC algorithms present")
    if has_hybrid:
        score -= 5
        drivers.append("Hybrid algorithms present")

    score = max(0, min(100, score))

    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "score": score,
        "level": level,
        "drivers": drivers,
    }
