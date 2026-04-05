"""PQC analysis engine for CycloneDX CBOM inputs."""

from __future__ import annotations

from typing import Any

from .parser import parse_cbom


_WEIGHTS = {
    "tls": 0.25,
    "cipher": 0.25,
    "kex": 0.20,
    "signature": 0.15,
    "key_size": 0.10,
    "certificate": 0.05,
}


def _adjust_weights(base: dict[str, float], context: dict[str, Any]) -> dict[str, float]:
    if not context:
        return base

    multipliers = {key: 1.0 for key in base}

    exposure = _normalise(context.get("exposure"))
    if exposure in {"public", "internet", "external"}:
        multipliers["tls"] *= 1.15
        multipliers["cipher"] *= 1.15
        multipliers["kex"] *= 1.10

    data_classification = _normalise(context.get("data_classification"))
    if data_classification in {"sensitive", "regulated", "pci", "pii", "banking"}:
        multipliers["signature"] *= 1.10
        multipliers["certificate"] *= 1.10
        multipliers["key_size"] *= 1.10

    environment = _normalise(context.get("environment"))
    if environment in {"prod", "production"}:
        multipliers["tls"] *= 1.10
        multipliers["cipher"] *= 1.10

    asset_type = _normalise(context.get("asset_type"))
    if asset_type in {"api", "gateway", "load_balancer"}:
        multipliers["cipher"] *= 1.05
        multipliers["kex"] *= 1.05

    adjusted = {key: base[key] * multipliers[key] for key in base}
    total = sum(adjusted.values()) or 1.0
    return {key: value / total for key, value in adjusted.items()}


def _normalise(value: Any) -> str:
    return str(value or "").strip().lower()


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _score_tls(tls_version: Any) -> tuple[int, list[str], list[str]]:
    tls = _normalise(tls_version)
    if "1.2" in tls:
        return 80, ["TLS 1.2 is outdated"], ["Upgrade to TLS 1.3"]
    if "1.3" in tls:
        return 0, [], []
    return 0, [], []


def _score_cipher(cipher: Any) -> tuple[int, list[str], list[str]]:
    c = _normalise(cipher)
    if "chacha20" in c:
        return 0, [], []
    if "rsa" in c:
        return 80, ["RSA cipher is vulnerable"], ["Replace RSA-based cipher with AES-GCM or PQC-safe suite"]
    if "aes" in c and "gcm" in c:
        return 0, [], []
    return 0, [], []


def _score_kex(key_exchange: Any) -> tuple[int, list[str], list[str]]:
    kex = _normalise(key_exchange)
    if "ml-kem" in kex or "kyber" in kex:
        return -20, [], []
    if "hybrid" in kex:
        return 10, [], []
    if "rsa" in kex:
        return 80, ["RSA key exchange is vulnerable"], ["Use ML-KEM (Kyber) for key exchange"]
    if "x25519" in kex:
        return 25, ["X25519 key exchange is classical"], ["Use ML-KEM (Kyber) or hybrid KEM"]
    if "ecdh" in kex or "ecdhe" in kex:
        return 30, ["ECDHE key exchange is partially vulnerable"], ["Use ML-KEM (Kyber) or hybrid KEM"]
    return 0, [], []


def _score_signature(signature_algorithm: Any) -> tuple[int, list[str], list[str]]:
    sig = _normalise(signature_algorithm)
    if "sha1" in sig:
        return 100, ["SHA1 signature is insecure"], ["Replace SHA1 with SHA256 or Dilithium"]
    if "ml-dsa" in sig or "dilithium" in sig or "falcon" in sig or "sphincs" in sig:
        return -20, [], []
    if "sha256" in sig:
        return 10, [], []
    if "rsa-pss" in sig:
        return 15, [], []
    if "ecdsa" in sig or "ed25519" in sig:
        return 15, [], []
    return 0, [], []


def _score_key_size(key_size: Any) -> tuple[int, list[str], list[str]]:
    raw = _normalise(key_size)
    if not raw:
        return 0, [], []

    if "pqc" in raw or "ml-kem" in raw or "kyber" in raw:
        return -15, [], []

    try:
        size = int(float(raw))
    except ValueError:
        return 0, [], []

    if size <= 2048:
        return 80, ["Key size 2048 is weak for PQC era"], ["Increase key size or migrate to PQC algorithms"]
    if size <= 3072:
        return 40, ["Key size 3072 is moderate for PQC era"], ["Consider 4096-bit RSA or PQC migration"]
    if size <= 4096:
        return 20, [], []

    return 0, [], []


def _score_certificate(certificate_algorithm: Any) -> tuple[int, list[str], list[str]]:
    cert = _normalise(certificate_algorithm)
    if "sha1" in cert:
        return 100, ["SHA1 certificate is insecure"], ["Replace SHA1 certificate with SHA256 or ML-DSA"]
    if "ml-dsa" in cert:
        return -20, [], []
    if "sha256" in cert:
        return 10, [], []
    if "ml-dsa" in cert:
        return -20, [], []
    return 0, [], []


def _extract_context(cbom_data: dict[str, Any], props: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    metadata = cbom_data.get("metadata")
    if isinstance(metadata, dict):
        for key in ("exposure", "data_classification", "asset_type", "environment"):
            value = metadata.get(key)
            if value:
                context[key] = value

    for key in ("exposure", "data_classification", "asset_type", "environment"):
        value = props.get(key)
        if value:
            context[key] = value

    return context


def _extract_properties(parsed: Any) -> list[dict[str, Any]]:
    if isinstance(parsed, dict) and "properties" in parsed:
        return [parsed.get("properties", {})]
    if isinstance(parsed, dict) and all(k in parsed for k in (
        "tls_version",
        "cipher",
        "key_exchange",
        "signature_algorithm",
        "key_size",
        "certificate_algorithm",
    )):
        return [parsed]
    if isinstance(parsed, list):
        props_list: list[dict[str, Any]] = []
        for item in parsed:
            if isinstance(item, dict):
                props = item.get("properties")
                if isinstance(props, dict):
                    props_list.append(props)
        return props_list
    return []


def analyze_pqc(cbom_data: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze PQC readiness from CycloneDX CBOM data.

    Returns a weighted risk score, status classification, issues, and recommendations.
    """
    parsed = parse_cbom(cbom_data)
    property_sets = _extract_properties(parsed)
    if not property_sets:
        property_sets = [{}]

    best_score = 0.0
    best_status = "PQC_READY"
    best_props: dict[str, Any] = property_sets[0]
    weak_points: list[str] = []
    recommendations: list[str] = []

    for props in property_sets:
        tls_score, tls_issues, tls_recs = _score_tls(props.get("tls_version"))
        cipher_score, cipher_issues, cipher_recs = _score_cipher(props.get("cipher"))
        kex_score, kex_issues, kex_recs = _score_kex(props.get("key_exchange"))
        sig_score, sig_issues, sig_recs = _score_signature(props.get("signature_algorithm"))
        key_size_score, key_size_issues, key_size_recs = _score_key_size(props.get("key_size"))
        cert_score, cert_issues, cert_recs = _score_certificate(props.get("certificate_algorithm"))

        weights = _adjust_weights(_WEIGHTS, _extract_context(cbom_data, props))
        weighted = (
            tls_score * weights["tls"]
            + cipher_score * weights["cipher"]
            + kex_score * weights["kex"]
            + sig_score * weights["signature"]
            + key_size_score * weights["key_size"]
            + cert_score * weights["certificate"]
        )

        risk_score = max(0.0, min(100.0, weighted))

        if risk_score <= 30:
            status = "PQC_READY"
        elif risk_score <= 60:
            status = "HYBRID"
        else:
            status = "VULNERABLE"

        if risk_score >= best_score:
            best_score = risk_score
            best_status = status
            best_props = props

        weak_points.extend(tls_issues + cipher_issues + kex_issues + sig_issues + key_size_issues + cert_issues)
        recommendations.extend(tls_recs + cipher_recs + kex_recs + sig_recs + key_size_recs + cert_recs)

    weak_points = _dedupe(weak_points)
    recommendations = _dedupe(recommendations)

    tls_norm = _normalise(best_props.get("tls_version"))
    has_tls12 = "1.2" in tls_norm
    combined_text = " ".join(_normalise(best_props.get(k)) for k in (
        "cipher",
        "key_exchange",
        "signature_algorithm",
        "certificate_algorithm",
    ))
    has_rsa = "rsa" in combined_text

    if has_tls12 and has_rsa:
        future_risk = "HIGH"
    elif best_status == "HYBRID":
        future_risk = "MEDIUM"
    else:
        future_risk = "LOW"

    if best_status == "PQC_READY":
        agility = "HIGH"
    elif best_status == "HYBRID":
        agility = "MEDIUM"
    else:
        agility = "LOW"

    return {
        "pqc_status": best_status,
        "risk_score": round(best_score, 2),
        "weak_points": weak_points,
        "recommendations": recommendations,
        "future_risk": future_risk,
        "agility": agility,
    }


def _run_test_cases() -> list[dict[str, Any]]:
    cases = [
        {
            "name": "TLS1.2 + RSA",
            "cbom": {
                "components": [
                    {
                        "name": "asset-1",
                        "properties": [
                            {"name": "tls_version", "value": "TLS 1.2"},
                            {"name": "cipher", "value": "RSA"},
                            {"name": "key_exchange", "value": "RSA"},
                            {"name": "signature_algorithm", "value": "SHA1"},
                            {"name": "key_size", "value": "2048"},
                            {"name": "certificate_algorithm", "value": "SHA1"},
                        ],
                    }
                ]
            },
        },
        {
            "name": "TLS1.3 + ECDHE",
            "cbom": {
                "components": [
                    {
                        "name": "asset-2",
                        "properties": [
                            {"name": "tls_version", "value": "TLS 1.3"},
                            {"name": "cipher", "value": "AES-256-GCM"},
                            {"name": "key_exchange", "value": "ECDHE"},
                            {"name": "signature_algorithm", "value": "SHA256"},
                            {"name": "key_size", "value": "3072"},
                            {"name": "certificate_algorithm", "value": "SHA256"},
                        ],
                    }
                ]
            },
        },
        {
            "name": "PQC values",
            "cbom": {
                "components": [
                    {
                        "name": "asset-3",
                        "properties": [
                            {"name": "tls_version", "value": "TLS 1.3"},
                            {"name": "cipher", "value": "AES-256-GCM"},
                            {"name": "key_exchange", "value": "ML-KEM-768"},
                            {"name": "signature_algorithm", "value": "Dilithium"},
                            {"name": "key_size", "value": "PQC"},
                            {"name": "certificate_algorithm", "value": "ML-DSA"},
                        ],
                    }
                ]
            },
        },
    ]

    results = []
    for case in cases:
        results.append({
            "case": case["name"],
            "result": analyze_pqc(case["cbom"]),
        })
    return results


if __name__ == "__main__":
    for output in _run_test_cases():
        print(output)
