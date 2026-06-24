"""Reproducibility capsule manifest."""

from __future__ import annotations

from pathlib import Path

from certgen.core.io import write_json


CAPSULE_REQUIREMENTS = ["command_index", "environment", "dependencies", "registry_templates", "feature_cache_schema", "preprocessing_locks", "run_plans", "certificate_configs", "report_commands", "evidence_policy", "limitations"]


def validate_capsule(root: str | Path = ".") -> dict:
    root = Path(root)
    missing = []
    checks = {
        "command_index": root / "docs/COMMAND_INDEX_V4.md",
        "registry_templates": root / "registry",
        "feature_cache_schema": root / "docs/FEATURE_CACHE_CONTRACT_V3.md",
        "preprocessing_locks": root / "configs/preprocessing_locks",
        "evidence_policy": root / "docs/CLAIM_POLICY_V3.md",
        "limitations": root / "docs/V4_SINGLE_FILE_HANDOFF.md",
    }
    for key, path in checks.items():
        if not path.exists():
            missing.append(key)
    return {"passed": not missing, "missing": missing, "claim_allowed": False, "evidence_status": "planned_only"}


def write_capsule_manifest(out: str | Path) -> dict:
    payload = {"capsule_requirements": CAPSULE_REQUIREMENTS, "claim_allowed": False, "evidence_status": "planned_only"}
    write_json(payload, out)
    return payload
