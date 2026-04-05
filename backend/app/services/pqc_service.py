"""Service layer for PQC analysis using CycloneDX CBOM data."""

from __future__ import annotations

from typing import Any

from app.pqc_engine.pqc_engine import analyze_pqc


class PQCService:
    """Facade for PQC analysis operations."""

    @staticmethod
    def analyze_cbom(cbom_data: dict[str, Any]) -> dict[str, Any]:
        return analyze_pqc(cbom_data)


def run_pqc_analysis(cbom_data: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper for direct PQC analysis calls."""
    return analyze_pqc(cbom_data)
