"""
compliance/labeling.py — PQC Compliance Labeling Service.

Validates each asset's cryptographic algorithm against:
  • NIST FIPS 203 (2024) — ML-KEM (Key Encapsulation Mechanism)
  • NIST FIPS 204 (2024) — ML-DSA (Digital Signature Algorithm)
  • NIST FIPS 205 (2024) — SLH-DSA (Stateless Hash-Based Digital Signature)
  • NIST SP 800-186      — Approved Elliptic Curves (reference for deprecation)
  • CNSA 2.0 (NSA)       — Commercial National Security Algorithm Suite

Issues strict three-state quantum labels:
  ┌─────────────────────────────────────────────────────────────┐
  │  FULLY_QUANTUM_SAFE   — NIST FIPS 203/204/205 approved only │
  │  PQC_READY            — Hybrid classical+PQC in use         │
  │  QUANTUM_VULNERABLE   — Classical-only (RSA, ECDH, DSA …)   │
  └─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Final

import structlog
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# NIST FIPS approved algorithm sets
# ─────────────────────────────────────────────────────────────────────────────

# FIPS 203 — ML-KEM (CRYSTALS-Kyber) key encapsulation
FIPS_203_APPROVED: Final[frozenset[str]] = frozenset({
    "ml-kem-512", "ml-kem-768", "ml-kem-1024",
    "kyber-512", "kyber-768", "kyber-1024",        # Pre-standardisation names
    "x25519kyber768",                               # Hybrid KEM (Chrome/TLS 1.3)
    "x25519mlkem768",                               # IETF draft hybrid
})

# FIPS 204 — ML-DSA (CRYSTALS-Dilithium) digital signatures
FIPS_204_APPROVED: Final[frozenset[str]] = frozenset({
    "ml-dsa-44", "ml-dsa-65", "ml-dsa-87",
    "dilithium2", "dilithium3", "dilithium5",       # Pre-standardisation names
})

# FIPS 205 — SLH-DSA (SPHINCS+) stateless hash-based signatures
FIPS_205_APPROVED: Final[frozenset[str]] = frozenset({
    "slh-dsa-sha2-128f", "slh-dsa-sha2-128s",
    "slh-dsa-sha2-192f", "slh-dsa-sha2-192s",
    "slh-dsa-sha2-256f", "slh-dsa-sha2-256s",
    "slh-dsa-shake-128f", "slh-dsa-shake-128s",
    "slh-dsa-shake-192f", "slh-dsa-shake-192s",
    "slh-dsa-shake-256f", "slh-dsa-shake-256s",
    "sphincs-sha2-128f", "sphincs-sha2-256f",       # Pre-standardisation names
})

# All approved PQC algorithms (union of all FIPS sets)
ALL_NIST_PQC_APPROVED: Final[frozenset[str]] = (
    FIPS_203_APPROVED | FIPS_204_APPROVED | FIPS_205_APPROVED
)

# Hybrid KEM patterns — classical + PQC combined ( earns PQC_READY, not FULLY_QUANTUM_SAFE)
HYBRID_KEM_PATTERNS: Final[frozenset[str]] = frozenset({
    "x25519kyber768", "x25519mlkem768",
    "p256kyber512", "p384kyber768", "p521kyber1024",
})

# CNSA 2.0 approved algorithms (NSA mandate for national security systems)
CNSA_2_APPROVED: Final[frozenset[str]] = frozenset({
    "ml-kem-1024", "ml-dsa-87",
    "slh-dsa-sha2-256f", "slh-dsa-shake-256f",
    "aes-256-gcm", "sha-384", "sha-512",
})

# Explicitly deprecated / non-compliant algorithms
DEPRECATED_ALGORITHMS: Final[frozenset[str]] = frozenset({
    "rsa-512", "rsa-1024",
    "dh-1024", "dh-512",
    "sha-1", "md5", "md4",
    "rc4", "des", "3des",
    "export-grade",
})

# ─────────────────────────────────────────────────────────────────────────────
# Label Definitions
# ─────────────────────────────────────────────────────────────────────────────

class QuantumLabel(str, enum.Enum):
    """Strict three-state quantum readiness label."""
    FULLY_QUANTUM_SAFE  = "fully_quantum_safe"   # NIST FIPS 203/204/205 only
    PQC_READY           = "pqc_ready"            # Hybrid classical+PQC
    QUANTUM_VULNERABLE  = "quantum_vulnerable"   # Classical-only


class ComplianceStandard(str, enum.Enum):
    FIPS_203  = "NIST_FIPS_203"
    FIPS_204  = "NIST_FIPS_204"
    FIPS_205  = "NIST_FIPS_205"
    CNSA_2    = "NSA_CNSA_2.0"
    NIST_SP_800_186 = "NIST_SP_800-186"


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Output Models
# ─────────────────────────────────────────────────────────────────────────────

class AlgorithmFinding(BaseModel):
    """Compliance finding for one algorithm."""
    algorithm:    str
    key_bits:     int | None = None
    is_approved:  bool
    is_hybrid:    bool
    is_deprecated: bool
    applicable_standards: list[ComplianceStandard]
    violations:   list[str]
    notes:        str


class ComplianceLabelResult(BaseModel):
    """Full compliance label output for one asset."""
    model_config = ConfigDict(from_attributes=True)

    asset_id:          uuid.UUID | None = None
    host:              str | None = None
    quantum_label:     QuantumLabel
    overall_compliant: bool
    cnsa2_compliant:   bool
    findings:          list[AlgorithmFinding]
    approved_count:    int
    hybrid_count:      int
    vulnerable_count:  int
    deprecated_count:  int
    summary:           str
    remediation_priority: str   # "immediate" | "planned" | "none"
    labeled_at:        datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# Compliance Labeling Engine
# ─────────────────────────────────────────────────────────────────────────────

class PQCComplianceLabeler:
    """
    Validates asset cryptographic algorithms against NIST FIPS 203/204/205
    and issues strict quantum-readiness labels.

    Usage::

        labeler = PQCComplianceLabeler()
        result = labeler.label_asset(
            algorithms=["rsa-2048", "ecdh-p256", "aes-256-gcm"],
            asset_id=uuid.uuid4(),
            host="api.pnb.co.in",
        )
    """

    @staticmethod
    def _normalise(algo: str) -> str:
        """Lowercase + strip whitespace + unify separators."""
        return algo.lower().strip().replace(" ", "-").replace("_", "-")

    def _assess_algorithm(self, raw_algo: str, key_bits: int | None = None) -> AlgorithmFinding:
        """Produce a compliance finding for a single algorithm."""
        algo    = self._normalise(raw_algo)
        violations: list[str] = []
        standards: list[ComplianceStandard] = []

        is_approved  = algo in ALL_NIST_PQC_APPROVED
        is_hybrid    = algo in HYBRID_KEM_PATTERNS
        is_deprecated = algo in DEPRECATED_ALGORITHMS

        # Identify applicable FIPS standards
        if algo in FIPS_203_APPROVED:
            standards.append(ComplianceStandard.FIPS_203)
        if algo in FIPS_204_APPROVED:
            standards.append(ComplianceStandard.FIPS_204)
        if algo in FIPS_205_APPROVED:
            standards.append(ComplianceStandard.FIPS_205)

        # Violation: deprecated algorithm in use
        if is_deprecated:
            violations.append(f"{raw_algo} is explicitly deprecated by NIST / NSA CNSA 2.0")

        # Violation: RSA in use with quantum-vulnerable key sizes
        if "rsa" in algo and not is_deprecated:
            bits = key_bits or 0
            if bits < 2048:
                violations.append(f"RSA key size {bits} < 2048-bit (NIST deprecated)")
            elif bits < 3072:
                violations.append(
                    f"RSA-{bits} is quantum-vulnerable; NIST recommends migration to ML-KEM by 2030"
                )
            else:
                violations.append("RSA family is quantum-vulnerable (Shor's algorithm applicable)")

        # Violation: ECDH/ECDSA without hybrid PQC
        if any(p in algo for p in ("ecdh", "ecdsa", "x25519", "x448", "ed25519")):
            if not is_hybrid and not is_approved:
                violations.append(
                    f"{raw_algo} is ECC-based and quantum-vulnerable without a PQC hybrid"
                )

        # Note for hybrid KEM: partially compliant
        notes = ""
        if is_hybrid:
            notes = "Hybrid KEM provides PQC_READY status — classical component still present"
        elif is_approved:
            notes = f"NIST-approved PQC algorithm under {', '.join(s.value for s in standards)}"
        elif not violations:
            notes = "Classical algorithm; not yet deprecated but quantum-vulnerable"

        return AlgorithmFinding(
            algorithm=raw_algo,
            key_bits=key_bits,
            is_approved=is_approved,
            is_hybrid=is_hybrid,
            is_deprecated=is_deprecated,
            applicable_standards=standards,
            violations=violations,
            notes=notes,
        )

    def label_asset(
        self,
        algorithms: list[str | dict[str, Any]],
        asset_id: uuid.UUID | None = None,
        host: str | None = None,
    ) -> ComplianceLabelResult:
        """
        Label an asset with its quantum-readiness status.

        Args:
            algorithms: List of algorithm identifiers (strings) OR dicts
                        with keys 'algo' and optionally 'key_bits'.
            asset_id:   Optional UUID for traceability.
            host:       Asset hostname for the report.

        Returns:
            ComplianceLabelResult with quantum label and per-algorithm findings.
        """
        # Normalise input — accept both str and {algo, key_bits} dicts
        parsed: list[tuple[str, int | None]] = []
        for item in algorithms:
            if isinstance(item, dict):
                parsed.append((item.get("algo", ""), item.get("key_bits")))
            else:
                parsed.append((str(item), None))

        findings = [self._assess_algorithm(a, k) for a, k in parsed if a]

        # Count categories
        approved_count    = sum(1 for f in findings if f.is_approved and not f.is_hybrid)
        hybrid_count      = sum(1 for f in findings if f.is_hybrid)
        vulnerable_count  = sum(1 for f in findings if not f.is_approved and not f.is_hybrid and not f.is_deprecated)
        deprecated_count  = sum(1 for f in findings if f.is_deprecated)
        total             = len(findings)

        # ── Three-state quantum label logic ──────────────────────────────────
        # FULLY_QUANTUM_SAFE:  all algorithms are NIST-approved PQC (no classical, no hybrid)
        # PQC_READY:           at least one hybrid KEM present AND no deprecated algos
        # QUANTUM_VULNERABLE:  any classical-only or deprecated algorithms detected

        has_deprecated   = deprecated_count > 0
        has_vulnerable   = vulnerable_count > 0
        has_hybrid       = hybrid_count > 0
        all_safe         = approved_count == total and total > 0

        if all_safe and not has_deprecated and not has_vulnerable:
            label = QuantumLabel.FULLY_QUANTUM_SAFE
        elif has_hybrid and not has_deprecated and (approved_count + hybrid_count) == total:
            label = QuantumLabel.PQC_READY
        else:
            label = QuantumLabel.QUANTUM_VULNERABLE

        # CNSA 2.0 compliance: ALL algorithms must be in CNSA_2_APPROVED set
        cnsa2_compliant = all(
            self._normalise(f.algorithm) in CNSA_2_APPROVED
            for f in findings
        )

        overall_compliant = label in (QuantumLabel.FULLY_QUANTUM_SAFE, QuantumLabel.PQC_READY)

        # Remediation priority
        if label == QuantumLabel.QUANTUM_VULNERABLE or has_deprecated:
            priority = "immediate"
        elif label == QuantumLabel.PQC_READY:
            priority = "planned"
        else:
            priority = "none"

        # Human-readable summary
        summary = (
            f"Asset {host or asset_id}: [{label.value.upper()}] "
            f"{approved_count} PQC-safe, {hybrid_count} hybrid, "
            f"{vulnerable_count} vulnerable, {deprecated_count} deprecated "
            f"out of {total} algorithms. "
            f"CNSA 2.0: {'✓' if cnsa2_compliant else '✗'}."
        )

        result = ComplianceLabelResult(
            asset_id=asset_id,
            host=host,
            quantum_label=label,
            overall_compliant=overall_compliant,
            cnsa2_compliant=cnsa2_compliant,
            findings=findings,
            approved_count=approved_count,
            hybrid_count=hybrid_count,
            vulnerable_count=vulnerable_count,
            deprecated_count=deprecated_count,
            summary=summary,
            remediation_priority=priority,
        )

        logger.info(
            "compliance_label_issued",
            asset_id=str(asset_id),
            host=host,
            label=label.value,
            priority=priority,
        )
        return result

    def label_batch(
        self,
        assets: list[dict[str, Any]],
    ) -> list[ComplianceLabelResult]:
        """
        Label multiple assets in batch.

        Each asset dict must have: 'algorithms' (list), optionally 'asset_id', 'host'.
        """
        return [
            self.label_asset(
                algorithms=asset["algorithms"],
                asset_id=asset.get("asset_id"),
                host=asset.get("host"),
            )
            for asset in assets
        ]
