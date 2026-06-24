"""V5 related-work board audit."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from certgen.core.io import write_json


RELATED_WORK_FIELDS = [
    "work_id",
    "title",
    "authors",
    "year",
    "venue",
    "url_or_doi",
    "bucket",
    "verified",
    "verification_source",
    "how_certgen_uses_it",
    "reviewer_attack_it_supports_or_defuses",
    "citation_status",
    "notes",
]

REQUIRED_BUCKETS = [
    "generative_image_metrics",
    "generative_video_metrics",
    "metric_reproducibility_preprocessing_sensitivity",
    "sequential_inference_anytime_valid_methods",
    "evaluation_reliability_benchmark_auditing",
    "preference_arena_evaluation_contrast",
]


def read_related_work_board(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def audit_related_work_board(path: str | Path = "registry/related_work/related_work_board_v5.csv", paper_root: str | Path = "paper") -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    path = Path(path)
    if not path.exists():
        return {"passed": False, "errors": [f"missing related-work board: {path}"], "warnings": [], "claim_allowed": False}
    rows = read_related_work_board(path)
    buckets = {row.get("bucket") for row in rows}
    for bucket in REQUIRED_BUCKETS:
        if bucket not in buckets:
            errors.append(f"missing related-work bucket: {bucket}")
    for idx, row in enumerate(rows, start=2):
        for field in RELATED_WORK_FIELDS:
            if field not in row:
                errors.append(f"row {idx}: missing field {field}")
        verified = row.get("verified", "").lower() == "true"
        if verified and (not row.get("url_or_doi") or not row.get("verification_source")):
            errors.append(f"row {idx}: verified citation requires URL/DOI and source")
        if row.get("citation_status") not in {"needs_verification", "verified", "not_cited"}:
            errors.append(f"row {idx}: invalid citation_status")
        if row.get("citation_status") == "verified" and not verified:
            errors.append(f"row {idx}: citation_status verified conflicts with verified=false")
    fake_cites = []
    paper_root = Path(paper_root)
    for file_path in paper_root.glob("**/*.tex") if paper_root.exists() else []:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        fake_cites.extend(f"{file_path}:{match.group(0)}" for match in re.finditer(r"\[[A-Z][A-Za-z]+20\d{2}\]", text))
    if fake_cites:
        errors.extend(f"fake placeholder citation outside scaffold: {item}" for item in fake_cites)
    return {"passed": not errors, "errors": errors, "warnings": warnings, "rows": len(rows), "claim_allowed": False, "evidence_status": "template_only"}


def render_related_work_board(csv_path: str | Path, out: str | Path, todo_out: str | Path | None = None) -> dict[str, Any]:
    rows = read_related_work_board(csv_path)
    by_bucket: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_bucket.setdefault(row["bucket"], []).append(row)
    lines = ["# Related Work Board V5", "", "`NO_FAKE_CITATIONS`", ""]
    todo = ["# Citation Verification TODO V5", ""]
    for bucket in sorted(by_bucket):
        lines.extend([f"## {bucket}", "", "| Work | Status | Use |", "|---|---|---|"])
        for row in sorted(by_bucket[bucket], key=lambda r: r["work_id"]):
            lines.append(f"| `{row['work_id']}` | `{row['citation_status']}` | {row['how_certgen_uses_it']} |")
            if row["citation_status"] == "needs_verification":
                todo.append(f"- {row['work_id']}: verify title/authors/year/venue/url before paper claim.")
        lines.append("")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    if todo_out:
        Path(todo_out).parent.mkdir(parents=True, exist_ok=True)
        Path(todo_out).write_text("\n".join(todo) + "\n", encoding="utf-8")
    return {"buckets": sorted(by_bucket), "rows": len(rows), "claim_allowed": False}


def write_related_work_audit(json_out: str | Path = "data/results/v5_related_work_audit.json") -> dict[str, Any]:
    payload = audit_related_work_board()
    write_json(payload, json_out)
    return payload
