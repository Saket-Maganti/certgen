"""Non-destructive repository inventory for the consolidated CertGen audit.

The inventory describes files; it does not promote any file to empirical
evidence.  It intentionally omits VCS internals and disposable interpreter
caches while retaining ignored scientific artifacts if they exist.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any


FIELDS = [
    "path",
    "purpose",
    "current_or_legacy",
    "source_or_generated",
    "evidence_class",
    "safe_to_release",
    "action_needed",
    "tracked",
    "ignored",
    "size_bytes",
]

SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".ipynb_checkpoints"}
def _git_paths(root: Path, *args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _purpose(path: Path) -> str:
    top = path.parts[0]
    return {
        "certgen": "package implementation",
        "tests": "automated verification",
        "configs": "execution configuration",
        "commands": "execution wrapper",
        "notebooks": "remote execution asset",
        "docs": "documentation or audit report",
        "paper": "manuscript source",
        "registry": "provenance or study registry",
        "data": "input, fixture, cache, or generated result",
        "reports": "consolidated forensic audit output",
        "release": "release contract or manifest",
    }.get(top, "repository metadata or historical process artifact")


def _lifecycle(path: Path) -> str:
    value = path.as_posix()
    if path.parts and path.parts[0].startswith("certgen_prompt_pack_v"):
        return "legacy"
    match = re.search(r"(?:^|[/_.-])[vV](\d+)(?:[/_.-]|$)", value)
    if match and int(match.group(1)) < 9:
        return "legacy"
    if value.startswith(("docs/R", "commands/r", "data/results/r")):
        return "legacy"
    return "current"


def _material(path: Path) -> str:
    value = path.as_posix()
    if value.startswith(("data/results/", "data/smoke/", "data/kaggle_", "data/imported/")):
        return "generated"
    if value.startswith("notebooks/generated/"):
        return "generated"
    if path.suffix in {".zip", ".npz", ".npy", ".pt", ".pth"}:
        return "generated"
    return "source"


def _json_evidence_class(path: Path) -> str | None:
    if path.suffix != ".json":
        return None
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    status = str(payload.get("evidence_status", "")).lower()
    if payload.get("claim_allowed") is True:
        return "PAPER_EVIDENCE_CANDIDATE_REQUIRES_REAUDIT"
    if any(token in status for token in ("synthetic", "smoke")):
        return "SYNTHETIC_ONLY"
    if any(token in status for token in ("template", "planned", "dry_run")):
        return "PLANNING_ONLY"
    if "run_log" in status:
        return "RUN_LOG_ONLY"
    if "real" in status or "pilot" in status:
        # A self-declared real/pilot label is not sufficient evidence.
        return "PILOT_ARTIFACT_REQUIRES_PROVENANCE_AUDIT"
    return None


def _evidence_class(path: Path, *, read_path: Path | None = None) -> str:
    value = path.as_posix()
    parsed = _json_evidence_class(read_path or path)
    if parsed:
        return parsed
    if value.startswith("data/smoke/") or "smoke" in path.name.lower():
        return "SYNTHETIC_ONLY"
    if value.startswith(("data/kaggle_inputs/", "data/kaggle_uploads/")):
        return "RUN_LOG_ONLY"
    if value.startswith("data/results/"):
        return "CACHE_ARTIFACT"
    if value.startswith("registry/"):
        return "PLANNING_ONLY"
    if value.startswith("paper/"):
        return "MISSING_EMPIRICAL_EVIDENCE"
    return "NOT_EVIDENCE"


def _safe_to_release(path: Path, lifecycle: str, material: str) -> bool:
    value = path.as_posix()
    if lifecycle == "legacy" or material == "generated":
        return False
    if value.startswith(("reports/", "certgen_prompt_pack_", "AUTORUN_")):
        return False
    if path.name == ".DS_Store":
        return False
    return value.startswith(("certgen/", "tests/", "configs/", "notebooks/kaggle/", "paper/", "release/")) or path.name in {
        "README.md",
        "LICENSE",
        "CITATION.cff",
        "pyproject.toml",
    }


def _action(path: Path, lifecycle: str, material: str, evidence_class: str, safe: bool) -> str:
    if path.name == ".DS_Store":
        return "exclude_from_release"
    if lifecycle == "legacy":
        return "retain_in_worktree_archive_from_public_release"
    if material == "generated":
        return "preserve_if_unique_register_hash_exclude_from_source_release"
    if evidence_class == "MISSING_EMPIRICAL_EVIDENCE":
        return "retain_placeholders_until_claim_gate_passes"
    if not safe:
        return "review_before_release"
    return "none"


def build_inventory(root: str | Path = ".") -> list[dict[str, Any]]:
    root = Path(root).resolve()
    tracked = _git_paths(root, "ls-files")
    ignored = _git_paths(root, "ls-files", "-o", "-i", "--exclude-standard")
    rows: list[dict[str, Any]] = []
    for absolute in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = absolute.relative_to(root)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        if absolute.name == ".DS_Store":
            continue
        value = relative.as_posix()
        lifecycle = _lifecycle(relative)
        material = _material(relative)
        evidence_class = _evidence_class(relative, read_path=absolute)
        safe = _safe_to_release(relative, lifecycle, material)
        rows.append(
            {
                "path": value,
                "purpose": _purpose(relative),
                "current_or_legacy": lifecycle,
                "source_or_generated": material,
                "evidence_class": evidence_class,
                "safe_to_release": str(safe).lower(),
                "action_needed": _action(relative, lifecycle, material, evidence_class, safe),
                "tracked": str(value in tracked).lower(),
                "ignored": str(value in ignored).lower(),
                "size_bytes": absolute.stat().st_size,
            }
        )
    return rows


def write_inventory(rows: list[dict[str, Any]], csv_out: str | Path, json_out: str | Path) -> None:
    csv_path = Path(csv_out)
    json_path = Path(json_out)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "schema_version": "certgen_forensic_inventory_v1",
        "file_count": len(rows),
        "tracked_count": sum(row["tracked"] == "true" for row in rows),
        "untracked_count": sum(row["tracked"] == "false" and row["ignored"] == "false" for row in rows),
        "ignored_count": sum(row["ignored"] == "true" for row in rows),
        "generated_count": sum(row["source_or_generated"] == "generated" for row in rows),
        "legacy_count": sum(row["current_or_legacy"] == "legacy" for row in rows),
        "claim_allowed": False,
        "inventory_is_empirical_evidence": False,
        "rows": rows,
    }
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create the non-evidence CertGen forensic file inventory.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--csv-out", default="reports/CERTGEN_REPOSITORY_INVENTORY.csv")
    parser.add_argument("--json-out", default="reports/CERTGEN_REPOSITORY_INVENTORY.json")
    args = parser.parse_args(argv)
    rows = build_inventory(args.root)
    write_inventory(rows, args.csv_out, args.json_out)
    print(f"inventory_files={len(rows)} claim_allowed=false")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
