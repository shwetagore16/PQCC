"""Report generation utilities (JSON + PDF) for PQC analysis."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def build_report_payload(asset: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset": asset,
        "analysis": analysis,
    }


def _flatten_report_lines(report: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    asset = report.get("asset", {})
    analysis = report.get("analysis", {})

    lines.append("Asset Details")
    lines.append(f"- id: {asset.get('id', 'unknown')}")
    lines.append(f"- value: {asset.get('asset_value', 'unknown')}")
    lines.append(f"- type: {asset.get('asset_type', 'unknown')}")
    lines.append(f"- organization: {asset.get('organization', 'unknown')}")
    lines.append("")
    lines.append("PQC Analysis")
    lines.append(f"- pqc_status: {analysis.get('pqc_status')}")
    lines.append(f"- risk_score: {analysis.get('risk_score')}")
    lines.append(f"- future_risk: {analysis.get('future_risk')}")
    lines.append(f"- future_risk_score: {analysis.get('future_risk_score')}")
    lines.append(f"- agility: {analysis.get('agility')}")
    lines.append("")

    hndl = analysis.get("hndl_score") or {}
    agility = analysis.get("crypto_agility_score") or {}
    lines.append("Advanced Scores")
    lines.append(f"- hndl_score: {hndl.get('score')}")
    lines.append(f"- crypto_agility_score: {agility.get('score')}")
    lines.append("")

    lines.append("Weak Points")
    for item in analysis.get("weak_points", []) or []:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("Recommendations")
    for item in analysis.get("recommendations", []) or []:
        lines.append(f"- {item}")
    lines.append("")

    remediation = analysis.get("remediation") or {}
    lines.append("Remediation")
    lines.append(f"- priority_level: {remediation.get('priority_level')}")
    lines.append(f"- suggested_action: {remediation.get('suggested_action')}")

    ml_label = analysis.get("pqc_ml_label")
    ml_conf = analysis.get("pqc_ml_confidence")
    false_pos = analysis.get("false_positive_flag")
    lines.append("")
    lines.append("ML Assessment")
    lines.append(f"- ml_label: {ml_label}")
    lines.append(f"- ml_confidence: {ml_conf}")
    lines.append(f"- false_positive_flag: {false_pos}")

    return lines


def render_report_pdf(report: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, "PQC Asset Report")
    y -= 24

    pdf.setFont("Helvetica", 10)
    for line in _flatten_report_lines(report):
        if not line:
            y -= 8
            continue
        pdf.drawString(40, y, line)
        y -= 14
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 50

    pdf.save()
    return buffer.getvalue()
