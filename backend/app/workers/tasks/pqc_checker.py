"""
Core logic for the PQC Compliance Checker and Risk Scoring Engine.
This module fulfills the requirement for validating NIST-standardized PQC algorithms.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List
import uuid

class PQCTier(Enum):
    TIER_1_ELITE = "Elite"      # TLS 1.3 + Kyber + High Entropy
    TIER_2_STANDARD = "Standard" # TLS 1.3/1.2 + Classic Strong Ciphers
    TIER_3_LEGACY = "Legacy"     # RSA < 2048 or TLS < 1.2
    CRITICAL = "Critical"        # Expired, Self-signed, or Weak Primitives

class PQCComplianceChecker:
    """
    Evaluates an asset's cryptographic profile against PQC and general security standards.
    """
    
    def __init__(self, raw_scan_data: Dict[str, Any]):
        self.data = raw_scan_data
        self.risk_score = 0
        self.findings = []

    def evaluate_compliance(self) -> Dict[str, Any]:
        # 1. TLS Version Validation
        tls_ver = self.data.get("tls_version", "unknown")
        if tls_ver == "TLSv1.3":
            self.risk_score += 0
        elif tls_ver == "TLSv1.2":
            self.risk_score += 15
            self.findings.append("TLS 1.2 detected; migration to 1.3 recommended for PQC alignment.")
        else:
            self.risk_score += 40
            self.findings.append(f"Insecure TLS Version: {tls_ver}")

        # 2. PQC Algorithm Verification (Kyber / Dilithium)
        key_exchange = self.data.get("key_exchange", "")
        if "kyber" in key_exchange.lower() or "dilithium" in key_exchange.lower():
            is_pqc_ready = True
            tier = PQCTier.TIER_1_ELITE
        else:
            is_pqc_ready = False
            tier = PQCTier.TIER_2_STANDARD if tls_ver == "TLSv1.3" else PQCTier.TIER_3_LEGACY

        # 3. Port Management (Requirements 4 & 5)
        open_ports = self.data.get("open_ports", [])
        critical_ports = {21, 23, 445, 3389}
        for port in open_ports:
            if port in critical_ports:
                self.risk_score += 25
                self.findings.append(f"CRITICAL: Non-essential port {port} is OPEN.")
                tier = PQCTier.CRITICAL

        # 4. Certificate Validity
        expiry = self.data.get("cert_expiry")
        if expiry and (expiry - datetime.utcnow()).days < 30:
            self.risk_score += 30
            self.findings.append("Certificate expiring soon (<30 days).")
            tier = PQCTier.CRITICAL

        # 5. Symmetric Key Strength
        key_size = self.data.get("symmetric_key_size", 0)
        if key_size < 256:
            self.risk_score += 20
            self.findings.append(f"Weak symmetric key size detected ({key_size} bits).")

        return {
            "pqc_ready": is_pqc_ready,
            "risk_score": min(self.risk_score, 100),
            "tier": tier.value,
            "findings": self.findings,
            "label": "PQC READY" if is_pqc_ready and tier != PQCTier.CRITICAL else "NON-PQC READY"
        }

# Example Usage
if __name__ == "__main__":
    mock_scan = {
        "tls_version": "TLSv1.3",
        "key_exchange": "X25519 + Kyber768 (Hybrid)",
        "open_ports": [443, 22],
        "cert_expiry": datetime.utcnow() + timedelta(days=90),
        "symmetric_key_size": 256
    }
    
    checker = PQCComplianceChecker(mock_scan)
    report = checker.evaluate_compliance()
    print(f"Status: {report['label']} | Tier: {report['tier']} | Score: {report['risk_score']}")
