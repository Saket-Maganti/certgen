"""Render V2 certificate cards."""

from __future__ import annotations

from pathlib import Path

from certgen.certs.fid_policy import fid_policy_summary
from certgen.core.enums import NON_EVIDENCE_STATUSES
from certgen.core.io import read_json
from certgen.gates.claim_gate import assert_claim_safe


REQUIRED_CERT_FIELDS = {
    "comparison_id",
    "metric_label",
    "feature_hashes",
    "evidence_status",
    "method_label",
    "theory_status",
    "alpha",
    "budget_units",
    "sample_units_seen",
    "mean_estimate",
    "lower",
    "upper",
    "decision",
    "claim_allowed",
    "limitations",
}


def render_certificate_card(certificate: dict) -> str:
    missing = sorted(REQUIRED_CERT_FIELDS - set(certificate))
    if missing:
        raise ValueError("malformed certificate missing fields: " + ", ".join(missing))
    evidence_status = certificate["evidence_status"]
    warning = "NOT PAPER EVIDENCE" if evidence_status in NON_EVIDENCE_STATUSES else "EVIDENCE STATUS REQUIRES REVIEW"
    fid_policy = fid_policy_summary(certificate["metric_label"])
    lines = [
        "# V2 Certificate Card",
        "",
        f"`{warning}`",
        "",
        f"- Comparison ID: `{certificate['comparison_id']}`",
        f"- Metric label: `{certificate['metric_label']}`",
        f"- Evidence status: `{evidence_status}`",
        f"- Method label: `{certificate['method_label']}`",
        f"- Theory status: `{certificate['theory_status']}`",
        f"- Alpha: `{certificate['alpha']}`",
        f"- Budget units: `{certificate['budget_units']}`",
        f"- Sample units seen: `{certificate['sample_units_seen']}`",
        f"- Mean estimate: `{certificate['mean_estimate']}`",
        f"- Interval: `[{certificate['lower']}, {certificate['upper']}]`",
        f"- Decision code: `{certificate['decision']}`",
        f"- Claim allowed: `{certificate['claim_allowed']}`",
        "",
        "## Feature Hashes",
    ]
    for key, value in sorted(certificate.get("feature_hashes", {}).items()):
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Limitations"])
    for limitation in certificate.get("limitations", []):
        lines.append(f"- {limitation}")
    if fid_policy["is_fid_like"]:
        lines.extend(
            [
                "",
                "## FID/FD Policy Warning",
                "",
                "FID-like metrics are descriptive-only in V2 and cannot be the sole basis for rigorous claims.",
            ]
        )
    markdown = "\n".join(lines) + "\n"
    assert_claim_safe(markdown, evidence_status=evidence_status)
    return markdown


def render_certificate_card_file(certificate_path: str, out_path: str) -> str:
    certificate = read_json(certificate_path)
    markdown = render_certificate_card(certificate)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(markdown, encoding="utf-8")
    return markdown
