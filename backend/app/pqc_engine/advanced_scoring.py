"""Advanced scoring helpers for HNDL, crypto agility, future risk, and remediation."""

from __future__ import annotations

from typing import Any

from .ml_classifier import predict_pqc_ready
from .policy_engine import evaluate_policy


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


def _extract_context(cbom_data: dict[str, Any], props: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    metadata = cbom_data.get("metadata")
    if isinstance(metadata, dict):
        for key in (
            "exposure",
            "data_classification",
            "asset_type",
            "environment",
            "data_sensitivity",
            "retention_years",
            "business_criticality",
            "algorithm_flexibility",
            "key_rotation",
            "cert_upgrade_ease",
        ):
            value = metadata.get(key)
            if value is not None:
                context[key] = value

    for key in (
        "exposure",
        "data_classification",
        "asset_type",
        "environment",
        "data_sensitivity",
        "retention_years",
        "business_criticality",
        "algorithm_flexibility",
        "key_rotation",
        "cert_upgrade_ease",
    ):
        value = props.get(key)
        if value is not None:
            context[key] = value

    return context


def _classify_encryption_type(props: dict[str, Any]) -> str:
    combined = " ".join(_normalise(props.get(k)) for k in (
        "cipher",
        "key_exchange",
        "signature_algorithm",
        "certificate_algorithm",
    ))

    if any(token in combined for token in ("ml-kem", "kyber", "dilithium", "falcon", "sphincs", "ml-dsa")):
        return "PQC"
    if "hybrid" in combined:
        return "Hybrid"
    if "ecc" in combined or "ecdsa" in combined or "ecdh" in combined or "ed25519" in combined:
        return "ECC"
    if "rsa" in combined:
        return "RSA"
    return "Unknown"


def compute_hndl_score(cbom_data: dict[str, Any], props: dict[str, Any]) -> dict[str, Any]:
    context = _extract_context(cbom_data, props)

    data_sensitivity = _normalise(context.get("data_sensitivity") or context.get("data_classification"))
    encryption_type = _classify_encryption_type(props)
    key_size = _parse_key_size(props.get("key_size"))
    exposure = _normalise(context.get("exposure"))
    retention_years = context.get("retention_years")

    try:
        retention_years = int(retention_years)
    except (TypeError, ValueError):
        retention_years = 5

    sensitivity_score = 100 if data_sensitivity in {"critical", "regulated", "pci", "pii", "banking"} else 60 if data_sensitivity in {"internal", "sensitive"} else 20

    if encryption_type == "PQC":
        encryption_score = 10
    elif encryption_type == "Hybrid":
        encryption_score = 30
    elif encryption_type == "ECC":
        encryption_score = 60
    elif encryption_type == "RSA":
        encryption_score = 80
    else:
        encryption_score = 50

    if key_size is None:
        key_size_score = 50
    elif key_size <= 2048:
        key_size_score = 90
    elif key_size <= 3072:
        key_size_score = 70
    elif key_size <= 4096:
        key_size_score = 50
    else:
        key_size_score = 30

    exposure_score = 90 if exposure in {"public", "internet", "external"} else 50 if exposure in {"internal", "private"} else 60

    if retention_years >= 10:
        retention_score = 90
    elif retention_years >= 5:
        retention_score = 70
    elif retention_years >= 2:
        retention_score = 50
    else:
        retention_score = 30

    weights = {
        "sensitivity": 0.25,
        "encryption_type": 0.25,
        "key_size": 0.20,
        "exposure": 0.20,
        "retention": 0.10,
    }

    score = (
        sensitivity_score * weights["sensitivity"]
        + encryption_score * weights["encryption_type"]
        + key_size_score * weights["key_size"]
        + exposure_score * weights["exposure"]
        + retention_score * weights["retention"]
    )

    return {
        "score": round(score, 2),
        "parameters": {
            "data_sensitivity": data_sensitivity or "unknown",
            "encryption_type": encryption_type,
            "key_size": key_size or "unknown",
            "exposure": exposure or "unknown",
            "retention_years": retention_years,
        },
        "weights": weights,
        "formula": "sum(param_score * weight)",
    }


def compute_crypto_agility_score(cbom_data: dict[str, Any], props: dict[str, Any]) -> dict[str, Any]:
    context = _extract_context(cbom_data, props)

    algorithm_flexibility = _normalise(context.get("algorithm_flexibility"))
    key_rotation = context.get("key_rotation")
    tls_version = _normalise(props.get("tls_version"))
    cert_upgrade_ease = _normalise(context.get("cert_upgrade_ease"))

    combined = " ".join(_normalise(props.get(k)) for k in (
        "cipher",
        "key_exchange",
        "signature_algorithm",
        "certificate_algorithm",
    ))
    hybrid_support = "hybrid" in combined or any(token in combined for token in ("ml-kem", "kyber", "dilithium", "falcon", "sphincs", "ml-dsa"))

    if algorithm_flexibility == "upgradeable":
        flexibility_score = 80
    elif algorithm_flexibility == "hardcoded":
        flexibility_score = 20
    else:
        flexibility_score = 50

    rotation_score = 80 if str(key_rotation).lower() in {"true", "1", "yes"} else 30

    if "1.3" in tls_version:
        tls_score = 90
    elif "1.2" in tls_version:
        tls_score = 60
    else:
        tls_score = 20

    hybrid_score = 80 if hybrid_support else 30

    if cert_upgrade_ease == "high":
        cert_score = 80
    elif cert_upgrade_ease == "low":
        cert_score = 20
    else:
        cert_score = 50

    weights = {
        "flexibility": 0.30,
        "rotation": 0.20,
        "tls": 0.20,
        "hybrid": 0.20,
        "cert": 0.10,
    }

    score = (
        flexibility_score * weights["flexibility"]
        + rotation_score * weights["rotation"]
        + tls_score * weights["tls"]
        + hybrid_score * weights["hybrid"]
        + cert_score * weights["cert"]
    )

    return {
        "score": round(score, 2),
        "parameters": {
            "algorithm_flexibility": algorithm_flexibility or "unknown",
            "key_rotation": bool(str(key_rotation).lower() in {"true", "1", "yes"}),
            "tls_version": tls_version or "unknown",
            "hybrid_support": hybrid_support,
            "cert_upgrade_ease": cert_upgrade_ease or "medium",
        },
        "weights": weights,
        "formula": "sum(param_score * weight)",
    }


def compute_future_risk(cbom_data: dict[str, Any], props: dict[str, Any]) -> dict[str, Any]:
    context = _extract_context(cbom_data, props)
    return evaluate_policy(props, context)


def compute_remediation_priority(risk_score: float, hndl_score: float, cbom_data: dict[str, Any], props: dict[str, Any]) -> dict[str, Any]:
    context = _extract_context(cbom_data, props)
    exposure = _normalise(context.get("exposure"))
    criticality = _normalise(context.get("business_criticality"))

    exposure_score = 100 if exposure in {"public", "internet", "external"} else 50

    if criticality in {"critical", "tier0", "tier1"}:
        criticality_score = 100
    elif criticality in {"high", "tier2"}:
        criticality_score = 70
    elif criticality in {"medium", "tier3"}:
        criticality_score = 50
    else:
        criticality_score = 40

    priority_score = (
        0.40 * risk_score
        + 0.30 * hndl_score
        + 0.20 * exposure_score
        + 0.10 * criticality_score
    )

    if priority_score >= 70:
        level = "HIGH"
        action = "Immediate remediation required"
    elif priority_score >= 40:
        level = "MEDIUM"
        action = "Plan remediation in next cycle"
    else:
        level = "LOW"
        action = "Monitor and schedule upgrades"

    auto_fix_eligible = level == "LOW" and risk_score <= 30

    return {
        "priority_score": round(priority_score, 2),
        "priority_level": level,
        "suggested_action": action,
        "auto_fix_eligible": auto_fix_eligible,
    }


def compute_ml_assessment(props: dict[str, Any]) -> dict[str, Any]:
    return predict_pqc_ready(props)
