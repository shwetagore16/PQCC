"""
ml_engine/hndl_scorer.py — HNDL (Harvest Now, Decrypt Later) Risk Scoring Service.

Implements the NIST MOSCA inequality:
    If  T_harvest + T_decrypt  <  T_migrate
    then the system is at HNDL risk — an adversary can harvest ciphertext today
    and later decrypt it once a Cryptographically Relevant Quantum Computer (CRQC)
    becomes available.

HNDL Score [0–10] is a composite of:
    • Quantum vulnerability of the algorithm (algo_risk)
    • Proximity to estimated CRQC break year (time_pressure)
    • Key size vs. NIST recommended minimum (key_strength)
    • Data sensitivity / exposure (context_weight)

Crypto-Agility Score [0–10] measures how easy the asset is to migrate:
    • Whether the protocol supports algorithm negotiation (e.g. TLS 1.3)
    • Whether a NIST PQC drop-in replacement exists
    • Historical migration cadence for this org

References:
    - NIST IR 8547 (2024) — Transition to PQC Standards
    - NIST SP 800-208 — Recommendation for Stateful Hash-Based Signature Schemes
    - Mosca, M. (2015) — Cybersecurity in an era with quantum computers
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

import structlog

from ml_engine.schemas import (
    HNDLScoreResult,
    MOSCAComponents,
    PQCSafetyLevel,
    RiskBand,
)

logger = structlog.get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Algorithm Catalogue
# Keys are canonical algorithm identifiers (lowercase, normalised).
# Values are AlgoProfile instances capturing quantum-era characteristics.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AlgoProfile:
    """Static cryptographic profile for one algorithm family."""
    name:               str
    safety_level:       PQCSafetyLevel
    # Year a CRQC of sufficient size is expected to break this algorithm
    # (pessimistic / conservative estimate aligned with MOSCA model).
    crqc_break_year:    int
    # Classical security level in bits (symmetric equivalent)
    classical_bits:     int
    # NIST-recommended minimum key size in bits for this family
    min_safe_key_bits:  int
    # Agility base score: how easily can this be swapped?
    agility_base:       float       # 0–10
    # Is a NIST-approved PQC replacement available right now?
    has_pqc_replacement: bool
    # Replacement algorithm name
    replacement:        str
    # Short rationale
    rationale:          str


# ── NIST PQC Safe algorithms (FIPS 203 / 204 / 205 — 2024) ──────────────────
_SAFE: Final[dict[str, AlgoProfile]] = {
    "ml-kem-512":      AlgoProfile("ML-KEM-512",      PQCSafetyLevel.QUANTUM_SAFE, 2100, 128, 256, 9.5, True, "ML-KEM-512",      "NIST FIPS 203 Level 1"),
    "ml-kem-768":      AlgoProfile("ML-KEM-768",      PQCSafetyLevel.QUANTUM_SAFE, 2100, 192, 256, 9.5, True, "ML-KEM-768",      "NIST FIPS 203 Level 3"),
    "ml-kem-1024":     AlgoProfile("ML-KEM-1024",     PQCSafetyLevel.QUANTUM_SAFE, 2100, 256, 256, 9.5, True, "ML-KEM-1024",     "NIST FIPS 203 Level 5"),
    "ml-dsa-44":       AlgoProfile("ML-DSA-44",       PQCSafetyLevel.QUANTUM_SAFE, 2100, 128, 256, 9.0, True, "ML-DSA-44",       "NIST FIPS 204 Level 2"),
    "ml-dsa-65":       AlgoProfile("ML-DSA-65",       PQCSafetyLevel.QUANTUM_SAFE, 2100, 192, 256, 9.0, True, "ML-DSA-65",       "NIST FIPS 204 Level 3"),
    "ml-dsa-87":       AlgoProfile("ML-DSA-87",       PQCSafetyLevel.QUANTUM_SAFE, 2100, 256, 256, 9.0, True, "ML-DSA-87",       "NIST FIPS 204 Level 5"),
    "slh-dsa-sha2-128f": AlgoProfile("SLH-DSA-SHA2-128f", PQCSafetyLevel.QUANTUM_SAFE, 2100, 128, 256, 7.5, True, "SLH-DSA",    "NIST FIPS 205"),
    "aes-256-gcm":     AlgoProfile("AES-256-GCM",     PQCSafetyLevel.QUANTUM_SAFE, 2100, 128, 256, 9.0, True, "AES-256-GCM",     "Grover halves key space; 256-bit remains safe"),
    "chacha20-poly1305": AlgoProfile("ChaCha20-Poly1305", PQCSafetyLevel.QUANTUM_SAFE, 2100, 128, 256, 9.0, True, "ChaCha20-Poly1305", "256-bit key; quantum safe"),
    "sha3-256":        AlgoProfile("SHA3-256",         PQCSafetyLevel.QUANTUM_SAFE, 2100, 128, 256, 9.0, True, "SHA3-256",        "128-bit quantum security"),
    "sha3-384":        AlgoProfile("SHA3-384",         PQCSafetyLevel.QUANTUM_SAFE, 2100, 192, 256, 9.0, True, "SHA3-384",        "192-bit quantum security"),
    "sha-384":         AlgoProfile("SHA-384",          PQCSafetyLevel.QUANTUM_SAFE, 2100, 192, 256, 9.0, True, "SHA-384",         "Grover-safe at 192-bit"),
    "sha-512":         AlgoProfile("SHA-512",          PQCSafetyLevel.QUANTUM_SAFE, 2100, 256, 256, 9.0, True, "SHA-512",         "Grover-safe at 256-bit"),
}

# ── Classical / quantum-vulnerable algorithms ────────────────────────────────
_CLASSICAL: Final[dict[str, AlgoProfile]] = {
    # RSA
    "rsa-512":    AlgoProfile("RSA-512",    PQCSafetyLevel.BROKEN,    2010, 0,   2048, 2.0, True, "ML-KEM-768", "Already classically broken"),
    "rsa-1024":   AlgoProfile("RSA-1024",   PQCSafetyLevel.BROKEN,    2020, 0,   2048, 2.5, True, "ML-KEM-768", "Classically weak; NIST deprecated"),
    "rsa-2048":   AlgoProfile("RSA-2048",   PQCSafetyLevel.CLASSICAL, 2030, 112, 2048, 5.0, True, "ML-KEM-768", "Shor's algorithm breaks at Q~4000 logical qubits"),
    "rsa-3072":   AlgoProfile("RSA-3072",   PQCSafetyLevel.CLASSICAL, 2032, 128, 3072, 5.5, True, "ML-KEM-768", "Marginally better; still vulnerable to Shor"),
    "rsa-4096":   AlgoProfile("RSA-4096",   PQCSafetyLevel.CLASSICAL, 2034, 140, 4096, 6.0, True, "ML-KEM-1024","Delayed but not immune to Shor"),
    "rsa-8192":   AlgoProfile("RSA-8192",   PQCSafetyLevel.CLASSICAL, 2038, 160, 8192, 5.0, True, "ML-KEM-1024","Large key cost; still Shor-vulnerable"),
    # ECDH / ECDSA
    "ecdh-p256":  AlgoProfile("ECDH-P256",  PQCSafetyLevel.CLASSICAL, 2030, 128, 384, 6.5, True, "ML-KEM-768", "Shor's on ECC: ~2330 logical qubits"),
    "ecdh-p384":  AlgoProfile("ECDH-P384",  PQCSafetyLevel.CLASSICAL, 2032, 192, 384, 7.0, True, "ML-KEM-1024","Better than P-256; still ECC"),
    "ecdh-p521":  AlgoProfile("ECDH-P521",  PQCSafetyLevel.CLASSICAL, 2035, 256, 521, 7.2, True, "ML-KEM-1024","Best classical ECC; still Shor-vulnerable"),
    "ecdsa-p256": AlgoProfile("ECDSA-P256", PQCSafetyLevel.CLASSICAL, 2030, 128, 384, 6.5, True, "ML-DSA-65",  "Replaces with ML-DSA"),
    "ecdsa-p384": AlgoProfile("ECDSA-P384", PQCSafetyLevel.CLASSICAL, 2032, 192, 384, 7.0, True, "ML-DSA-65",  "Replaces with ML-DSA"),
    "x25519":     AlgoProfile("X25519",     PQCSafetyLevel.CLASSICAL, 2031, 128, 255, 7.5, True, "ML-KEM-768", "Fast; quantum-vulnerable"),
    "x448":       AlgoProfile("X448",       PQCSafetyLevel.CLASSICAL, 2033, 224, 448, 7.5, True, "ML-KEM-1024","Larger Curve448; still vulnerable"),
    "ed25519":    AlgoProfile("Ed25519",    PQCSafetyLevel.CLASSICAL, 2031, 128, 255, 7.5, True, "ML-DSA-65",  "Edwards-form; still Shor-vulnerable"),
    # DH
    "dh-1024":    AlgoProfile("DH-1024",    PQCSafetyLevel.BROKEN,    2020, 0,   2048, 2.0, True, "ML-KEM-768", "Classically weak; NIST deprecated"),
    "dh-2048":    AlgoProfile("DH-2048",    PQCSafetyLevel.CLASSICAL, 2030, 112, 2048, 4.5, True, "ML-KEM-768", "Shor attack applicable"),
    "dh-4096":    AlgoProfile("DH-4096",    PQCSafetyLevel.CLASSICAL, 2035, 140, 4096, 5.0, True, "ML-KEM-1024","Extended lifetime; still vulnerable"),
    # Symmetric — weak
    "aes-128-gcm": AlgoProfile("AES-128-GCM", PQCSafetyLevel.CLASSICAL, 2035, 64, 256, 8.0, True, "AES-256-GCM","Grover halves to 64-bit; upgrade key size"),
    "sha-256":     AlgoProfile("SHA-256",     PQCSafetyLevel.CLASSICAL, 2040, 128, 384, 8.5, True, "SHA-384",    "Grover reduces to 128-bit; watch CRQC timeline"),
    "sha-1":       AlgoProfile("SHA-1",       PQCSafetyLevel.BROKEN,    2017, 0,   256, 2.0, True, "SHA3-256",   "Classically broken (SHAttered collision)"),
    "md5":         AlgoProfile("MD5",         PQCSafetyLevel.BROKEN,    2005, 0,   256, 1.0, True, "SHA3-256",   "Classically broken"),
    # Legacy
    "3des":        AlgoProfile("3DES",        PQCSafetyLevel.BROKEN,    2016, 0,   256, 1.5, True, "AES-256-GCM","NIST deprecated 2023"),
    "rc4":         AlgoProfile("RC4",         PQCSafetyLevel.BROKEN,    2013, 0,   256, 1.0, True, "ChaCha20-Poly1305","Prohibited by RFC 7465"),
}

ALGO_CATALOGUE: Final[dict[str, AlgoProfile]] = {**_SAFE, **_CLASSICAL}


# ─────────────────────────────────────────────────────────────────────────────
# MOSCA Inequality Parameters
# ─────────────────────────────────────────────────────────────────────────────

# Current year — used throughout scoring
_CURRENT_YEAR: Final[int] = datetime.utcnow().year

# Baseline CRQC arrival estimates (years from now)
# Conservative: IBM & NIST trajectories suggest 2030–2035 for a fault-tolerant CRQC
CRQC_ARRIVAL_PESSIMISTIC: Final[int] = 2030   # P10 scenario
CRQC_ARRIVAL_MEDIAN:      Final[int] = 2033   # P50 scenario
CRQC_ARRIVAL_OPTIMISTIC:  Final[int] = 2038   # P90 scenario

# Typical banking PQC migration timelines (years needed)
# Based on RBI/BIS guidance and industry benchmarks
MIGRATION_YEARS_BY_COMPLEXITY: Final[dict[str, float]] = {
    "low":      2.0,    # Library swap with PQC drop-in (e.g. liboqs + OpenSSL)
    "medium":   4.0,    # Protocol renegotiation, HSM upgrade
    "high":     6.0,    # Application re-architecture, CA reprovision
    "critical": 9.0,    # Core banking system overhaul, hardware replacement
}

# Harvest window: how long might an adversary have been storing ciphertext?
DEFAULT_HARVEST_YEARS: Final[float] = 5.0  # Conservative assumption


# ─────────────────────────────────────────────────────────────────────────────
# HNDLScorer
# ─────────────────────────────────────────────────────────────────────────────

class HNDLScorer:
    """
    Compute HNDL risk and crypto-agility scores per algorithm / asset.

    Usage::

        scorer = HNDLScorer()
        result = scorer.score("rsa-2048", key_bits=2048, asset_id=some_uuid)
        print(result.model_dump_json(indent=2))
    """

    def __init__(
        self,
        migration_complexity: str = "medium",
        harvest_years: float = DEFAULT_HARVEST_YEARS,
        crqc_scenario: str = "pessimistic",
    ) -> None:
        """
        Args:
            migration_complexity: One of 'low' | 'medium' | 'high' | 'critical'.
                Drives T_migrate in the MOSCA inequality.
            harvest_years: T_harvest — years of already-captured ciphertext at risk.
            crqc_scenario: 'pessimistic' (2030) | 'median' (2033) | 'optimistic' (2038).
        """
        self.migration_complexity = migration_complexity
        self.harvest_years = harvest_years
        self.crqc_scenario = crqc_scenario
        self._t_migrate = MIGRATION_YEARS_BY_COMPLEXITY.get(migration_complexity, 4.0)

    def _resolve_profile(self, algo_key: str, key_bits: int) -> AlgoProfile:
        """
        Resolve the AlgoProfile for a given algorithm identifier.
        Falls back to a generic classical profile if key is not in catalogue.
        """
        normalised = algo_key.lower().replace(" ", "-").replace("_", "-")

        # Direct catalogue lookup
        if normalised in ALGO_CATALOGUE:
            return ALGO_CATALOGUE[normalised]

        # Try matching by prefix (e.g. 'rsa' → nearest rsa entry)
        for key, profile in ALGO_CATALOGUE.items():
            if normalised.startswith(key.split("-")[0]):
                return profile

        logger.warning("algo_not_in_catalogue", algo=algo_key, key_bits=key_bits)
        # Synthetic unknown profile
        return AlgoProfile(
            name=algo_key,
            safety_level=PQCSafetyLevel.CLASSICAL,
            crqc_break_year=2031,
            classical_bits=max(56, key_bits // 2),
            min_safe_key_bits=256,
            agility_base=5.0,
            has_pqc_replacement=False,
            replacement="ML-KEM-768",
            rationale="Algorithm not in catalogue — defaulting to classical vulnerable profile",
        )

    def _compute_mosca(self, profile: AlgoProfile, key_bits: int) -> MOSCAComponents:
        """
        Compute MOSCA inequality components T_harvest, T_decrypt, T_migrate.

        T_decrypt = years until CRQC can break this algo at this key size.
        We model this as (crqc_break_year - current_year) clamped to [0, ∞).
        """
        crqc_break = profile.crqc_break_year  # from the static profile

        # Key-size adjustment: larger keys push the break year slightly further
        # Formula: each doubling of key bits beyond minimum adds ~1 year
        if key_bits > profile.min_safe_key_bits and profile.safety_level != PQCSafetyLevel.QUANTUM_SAFE:
            ratio = key_bits / profile.min_safe_key_bits
            key_bonus = math.log2(ratio) * 1.5
        else:
            key_bonus = 0.0

        adjusted_break = crqc_break + key_bonus
        t_decrypt = max(0.0, adjusted_break - _CURRENT_YEAR)

        mosca_risk = (self.harvest_years + t_decrypt) < self._t_migrate

        return MOSCAComponents(
            T_harvest=round(self.harvest_years, 2),
            T_decrypt=round(t_decrypt, 2),
            T_migrate=round(self._t_migrate, 2),
            mosca_risk=mosca_risk,
        )

    def _compute_hndl_score(
        self,
        profile: AlgoProfile,
        mosca: MOSCAComponents,
        key_bits: int,
    ) -> float:
        """
        Composite HNDL score [0–10].

        Components:
          algo_risk     [0–4]: intrinsic quantum vulnerability of this algorithm family
          time_pressure [0–3]: proximity to CRQC break year (higher = closer)
          key_weakness  [0–2]: how far below NIST minimum is this key size
          mosca_penalty [0–1]: binary bonus if MOSCA inequality is breached
        """
        # 1. Algo risk (based on safety level)
        algo_risk_map = {
            PQCSafetyLevel.BROKEN:       4.0,
            PQCSafetyLevel.CLASSICAL:    3.0,
            PQCSafetyLevel.HYBRID:       1.0,
            PQCSafetyLevel.QUANTUM_SAFE: 0.0,
        }
        algo_risk = algo_risk_map[profile.safety_level]

        # 2. Time pressure: urgency as CRQC arrival approaches
        years_remaining = max(0.0, mosca.T_decrypt)
        time_pressure = 3.0 * math.exp(-years_remaining / 10.0)  # decays over ~10-year horizon

        # 3. Key weakness penalty
        if key_bits < profile.min_safe_key_bits and profile.safety_level != PQCSafetyLevel.QUANTUM_SAFE:
            weakness_ratio = (profile.min_safe_key_bits - key_bits) / profile.min_safe_key_bits
            key_weakness = min(2.0, 2.0 * weakness_ratio)
        else:
            key_weakness = 0.0

        # 4. MOSCA breach binary penalty
        mosca_penalty = 1.0 if mosca.mosca_risk else 0.0

        raw = algo_risk + time_pressure + key_weakness + mosca_penalty
        return round(min(10.0, raw), 2)

    def _compute_agility_score(self, profile: AlgoProfile, key_bits: int) -> float:
        """
        Crypto-agility score [0–10]. Higher = easier to migrate.

        Factors:
          - Base agility from catalogue profile
          - Penalise if key is non-standard size (implies custom implementation)
          - Bonus if protocol supports algorithm negotiation
          - Bonus if PQC replacement exists right now
        """
        base = profile.agility_base

        # Key-size penalty: non-power-of-two or unusual keys suggest custom code
        is_standard_key = key_bits in {128, 192, 256, 384, 521, 1024, 2048, 3072, 4096, 8192}
        non_standard_penalty = 0.0 if is_standard_key else 1.0

        # PQC replacement availability bonus
        replacement_bonus = 1.0 if profile.has_pqc_replacement else 0.0

        score = base - non_standard_penalty + replacement_bonus
        return round(min(10.0, max(0.0, score)), 2)

    def _risk_band(self, hndl_score: float) -> RiskBand:
        if hndl_score >= 8.0:
            return RiskBand.CRITICAL
        elif hndl_score >= 6.0:
            return RiskBand.HIGH
        elif hndl_score >= 4.0:
            return RiskBand.MEDIUM
        return RiskBand.LOW

    def score(
        self,
        algo: str,
        key_bits: int,
        asset_id: uuid.UUID | None = None,
        migration_complexity: str | None = None,
        context_note: str = "",
    ) -> HNDLScoreResult:
        """
        Compute the full HNDL risk profile for one algorithm / key-size combination.

        Args:
            algo:                 Normalised algorithm identifier  (e.g. 'rsa-2048').
            key_bits:             Key size in bits.
            asset_id:             Optional asset UUID for traceability.
            migration_complexity: Override instance-level migration complexity.
            context_note:         Optional additional context appended to rationale.

        Returns:
            HNDLScoreResult — structured Pydantic model ready for JSON serialisation.
        """
        if migration_complexity:
            self._t_migrate = MIGRATION_YEARS_BY_COMPLEXITY.get(migration_complexity, self._t_migrate)

        profile   = self._resolve_profile(algo, key_bits)
        mosca     = self._compute_mosca(profile, key_bits)
        hndl      = self._compute_hndl_score(profile, mosca, key_bits)
        agility   = self._compute_agility_score(profile, key_bits)
        band      = self._risk_band(hndl)

        # Build rationale
        crqc_year = profile.crqc_break_year
        rationale = (
            f"{profile.name} (key={key_bits}b) is classified as "
            f"{profile.safety_level.value}. "
            f"Estimated CRQC break year: {crqc_year}. "
            f"MOSCA: T_harvest={mosca.T_harvest}y + T_decrypt={mosca.T_decrypt}y "
            f"{'<' if mosca.mosca_risk else '>='} T_migrate={mosca.T_migrate}y — "
            f"{'⚠ EXPOSED (harvest window breached)' if mosca.mosca_risk else '✓ within migration window'}. "
            f"Recommended replacement: {profile.replacement}. "
            f"{profile.rationale}. {context_note}".strip()
        )

        result = HNDLScoreResult(
            asset_id=asset_id,
            algo=profile.name,
            key_bits=key_bits,
            quantum_safe=profile.safety_level == PQCSafetyLevel.QUANTUM_SAFE,
            safety_level=profile.safety_level,
            expiry_year=profile.crqc_break_year,
            hndl_score=hndl,
            agility_score=agility,
            risk_band=band,
            mosca=mosca,
            rationale=rationale,
        )

        logger.info(
            "hndl_scored",
            algo=profile.name,
            key_bits=key_bits,
            hndl_score=hndl,
            band=band.value,
            mosca_risk=mosca.mosca_risk,
        )
        return result

    def score_batch(
        self,
        algorithms: list[dict],
        asset_id: uuid.UUID | None = None,
    ) -> list[HNDLScoreResult]:
        """
        Score a list of algorithm dicts.

        Each dict must have keys: 'algo' (str) and 'key_bits' (int).
        Optional keys: 'migration_complexity', 'context_note'.
        """
        return [
            self.score(
                algo=item["algo"],
                key_bits=item["key_bits"],
                asset_id=asset_id,
                migration_complexity=item.get("migration_complexity"),
                context_note=item.get("context_note", ""),
            )
            for item in algorithms
        ]

    @staticmethod
    def aggregate_asset_score(scores: list[HNDLScoreResult]) -> float:
        """
        Aggregate multiple per-algorithm HNDL scores into a single asset-level score.

        Uses a risk-weighted combination: the highest-risk algorithm dominates
        (max-pooling) but the average of the top-3 is also factored in to
        reward consistently weak crypto postures.
        """
        if not scores:
            return 0.0
        sorted_scores = sorted([s.hndl_score for s in scores], reverse=True)
        top_3_avg = sum(sorted_scores[:3]) / min(len(sorted_scores), 3)
        return round(0.6 * sorted_scores[0] + 0.4 * top_3_avg, 2)
