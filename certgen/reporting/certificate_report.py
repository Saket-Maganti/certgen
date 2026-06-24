"""Markdown rendering for decision certificates."""

from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any

from certgen.core.enums import EvidenceStatus
from certgen.core.io import to_json_dict


def _as_dict(certificate: Any) -> dict[str, Any]:
    if isinstance(certificate, dict):
        return certificate
    if is_dataclass(certificate):
        return to_json_dict(certificate)
    raise TypeError(f"Unsupported certificate type: {type(certificate).__name__}")


def certificate_report_markdown(certificate: Any) -> str:
    data = _as_dict(certificate)
    title = "NON-EVIDENCE SMOKE REPORT" if data.get("evidence_status") == EvidenceStatus.NON_EVIDENCE_SMOKE.value else "Certificate Report"
    lines = [
        f"# {title}",
        "",
        "This smoke artifact is for contract validation only.",
        "",
        f"- Comparison id: `{data.get('comparison_id')}`",
        f"- Metric: `{data.get('metric_name')}`",
        f"- Alpha: `{data.get('alpha')}`",
        f"- Status code: `{data.get('status')}`",
        f"- Sample budget: `{data.get('max_samples')}`",
        f"- N at decision: `{data.get('n_at_decision')}`",
        f"- Optional-stopping validity flag: `{data.get('optional_stopping_valid')}`",
        f"- Evidence status: `{data.get('evidence_status')}`",
        f"- FID rigor status: `{data.get('fid_rigor_status')}`",
        f"- Interval lower: `{data.get('lower')}`",
        f"- Interval upper: `{data.get('upper')}`",
        f"- Point estimate: `{data.get('point_estimate')}`",
        "",
        "## Limitations",
    ]
    for limitation in data.get("limitations", []):
        lines.append(f"- {limitation}")
    lines.extend(["", "## Provenance"])
    provenance = data.get("provenance") or {}
    for key in sorted(provenance):
        lines.append(f"- {key}: `{provenance[key]}`")
    lines.append("")
    return "\n".join(lines)
