"""Service layer for PQC analysis using CycloneDX CBOM data."""

from __future__ import annotations

from typing import Any

from app.pqc_engine.pqc_engine import analyze_pqc
from app.services.cache_service import get_cached_result, make_cbom_cache_key, set_cached_result


class PQCService:
    """Facade for PQC analysis operations."""

    @staticmethod
    def analyze_cbom(cbom_data: dict[str, Any]) -> dict[str, Any]:
        cache_key = make_cbom_cache_key(cbom_data)
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        result = analyze_pqc(cbom_data)
        set_cached_result(cache_key, result)
        return result


def run_pqc_analysis(cbom_data: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper for direct PQC analysis calls."""
    return analyze_pqc(cbom_data)
