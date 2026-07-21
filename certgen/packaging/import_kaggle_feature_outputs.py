"""Validate/import copied-back Kaggle feature output zips."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

from certgen.packaging.common import has_claim_allowed_true, inspect_zip_safety


REQUIRED_ROLES = {"reference", "google_ddpm", "frank_ddpm_ema", "frank_cfm"}
REQUIRED_FAMILIES = {"inception", "clip"}


def inspect_feature_zip(zip_path: str | Path) -> dict[str, Any]:
    path = Path(zip_path)
    if not path.exists():
        return {
            "status": "blocked",
            "blocker_code": "BLOCKED_FEATURE_OUTPUT_ZIP_MISSING",
            "claim_allowed": False,
            "evidence_status": "NO_REAL_EVIDENCE",
        }
    try:
        with zipfile.ZipFile(path) as archive:
            safety = inspect_zip_safety(path)
            if not safety["passed"]:
                return {
                    "status": "blocked",
                    "blocker_code": "BLOCKED_FEATURE_OUTPUT_CORRUPT",
                    "errors": safety["errors"],
                    "claim_allowed": False,
                    "evidence_status": "NO_REAL_EVIDENCE",
                }
            members = archive.namelist()
            text = "\n".join(members).lower()
            roles_present = sorted(role for role in REQUIRED_ROLES if role in text)
            families_present = sorted(family for family in REQUIRED_FAMILIES if family in text)
            missing_roles = sorted(REQUIRED_ROLES - set(roles_present))
            missing_families = sorted(REQUIRED_FAMILIES - set(families_present))
            missing_cache_files = sorted(
                f"{role}_{family}.{suffix}"
                for role in REQUIRED_ROLES
                for family in REQUIRED_FAMILIES
                for suffix in ["npz", "sidecar.json"]
                if f"{role}_{family}.{suffix}" not in text
            )
            status_names = [name for name in members if name.endswith("feature_extraction_status.json")]
            status: dict[str, Any] = {}
            if len(status_names) == 1:
                try:
                    loaded = json.loads(archive.read(status_names[0]).decode("utf-8"))
                    if isinstance(loaded, dict):
                        status = loaded
                except (UnicodeDecodeError, json.JSONDecodeError):
                    status = {}
            claim_true = False
            for name in members:
                if not name.endswith(".json"):
                    continue
                try:
                    loaded = json.loads(archive.read(name).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                claim_true = claim_true or has_claim_allowed_true(loaded)
            complete_status = (
                status.get("status_code") == "FEATURE_EXTRACTION_SHARDS_COMPLETE"
                and status.get("claim_allowed") is False
            )
            blocker = None if not missing_roles and not missing_families and not missing_cache_files and complete_status and not claim_true else "BLOCKED_FEATURE_CACHE_INVALID"
            return {
                "status": "ready" if blocker is None else "blocked",
                "blocker_code": blocker,
                "member_count": len(members),
                "roles_present": roles_present,
                "feature_families_present": families_present,
                "missing_roles": missing_roles,
                "missing_feature_families": missing_families,
                "missing_cache_files": missing_cache_files,
                "status_code": status.get("status_code"),
                "next_status": "READY_FOR_METRIC_SANITY_GATES" if blocker is None else None,
                "claim_allowed": False,
                "evidence_status": "run_log_only",
            }
    except (OSError, zipfile.BadZipFile):
        return {
            "status": "blocked",
            "blocker_code": "BLOCKED_FEATURE_OUTPUT_CORRUPT",
            "claim_allowed": False,
            "evidence_status": "NO_REAL_EVIDENCE",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    parser.add_argument("--out-json", default="data/results/v7_feature_import_summary.json")
    args = parser.parse_args(argv)
    payload = inspect_feature_zip(args.zip)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ready" else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
