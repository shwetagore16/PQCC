from app.pqc_engine.advanced_scoring import (
    compute_crypto_agility_score,
    compute_hndl_score,
    compute_ml_assessment,
    compute_future_risk,
)


def test_hndl_score_range():
    cbom_data = {
        "metadata": {
            "data_sensitivity": "critical",
            "exposure": "internet",
            "retention_years": 10,
        }
    }
    props = {
        "tls_version": "TLS 1.2",
        "key_exchange": "RSA",
        "signature_algorithm": "SHA1",
        "key_size": "1024",
    }

    result = compute_hndl_score(cbom_data, props)
    assert 0 <= result["score"] <= 100


def test_crypto_agility_score_range():
    cbom_data = {
        "metadata": {
            "algorithm_flexibility": "upgradeable",
            "key_rotation": True,
            "cert_upgrade_ease": "high",
        }
    }
    props = {
        "tls_version": "TLS 1.3",
        "key_exchange": "ML-KEM-768",
        "signature_algorithm": "Dilithium",
    }

    result = compute_crypto_agility_score(cbom_data, props)
    assert 0 <= result["score"] <= 100


def test_ml_assessment_returns_label_and_confidence():
    props = {
        "tls_version": "TLS 1.2",
        "key_exchange": "RSA",
        "signature_algorithm": "SHA1",
        "key_size": "1024",
    }

    result = compute_ml_assessment(props)
    assert result["label"] in {"PQC_READY", "NOT_READY"}
    assert 0.0 <= result["confidence"] <= 1.0


def test_future_risk_policy_output():
    cbom_data = {}
    props = {
        "tls_version": "TLS 1.0",
        "key_exchange": "RSA",
        "signature_algorithm": "SHA1",
        "key_size": "1024",
    }

    result = compute_future_risk(cbom_data, props)
    assert 0 <= result["score"] <= 100
    assert result["level"] in {"LOW", "MEDIUM", "HIGH"}
