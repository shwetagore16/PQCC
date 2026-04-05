"""CycloneDX CBOM parser for PQC analysis."""

from __future__ import annotations

from typing import Any


def parse_cbom(cbom_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Parse CycloneDX CBOM and normalise component properties.

    Returns a list of dicts:
      [{"component": <raw_component>, "properties": {"k": "v", ...}}, ...]
    """
    if not cbom_data:
        return []

    components = cbom_data.get("components") or []
    parsed: list[dict[str, Any]] = []

    for component in components:
        raw_properties = component.get("properties") or []
        properties: dict[str, Any] = {}

        if isinstance(raw_properties, dict):
            properties = raw_properties
        else:
            for prop in raw_properties:
                name = prop.get("name") if isinstance(prop, dict) else None
                if not name:
                    continue
                properties[name] = prop.get("value")

        parsed.append({
            "component": component,
            "properties": properties,
        })

    return parsed
