"""Validate/import copied-back Kaggle generation output zips."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

from certgen.packaging.common import has_claim_allowed_true, inspect_zip_safety


EXPECTED_SHARDS = {
    "google_ddpm_gpu0",
    "google_ddpm_gpu1",
    "frank_ddpm_ema_gpu0",
    "frank_ddpm_ema_gpu1",
    "frank_cfm_gpu0",
    "frank_cfm_gpu1",
}


def inspect_generation_zip(zip_path: str | Path) -> dict[str, Any]:
    path = Path(zip_path)
    if not path.exists():
        return {
            "status": "blocked",
            "blocker_code": "BLOCKED_GENERATION_OUTPUT_ZIP_MISSING",
            "claim_allowed": False,
            "evidence_status": "NO_REAL_EVIDENCE",
        }
    try:
        with zipfile.ZipFile(path) as archive:
            safety = inspect_zip_safety(path)
            if not safety["passed"]:
                return {
                    "status": "blocked",
                    "blocker_code": "BLOCKED_GENERATION_OUTPUT_CORRUPT",
                    "errors": safety["errors"],
                    "claim_allowed": False,
                    "evidence_status": "NO_REAL_EVIDENCE",
                }
            members = archive.namelist()
            lowered = "\n".join(members).lower()
            has_manifest = any(name.endswith(".jsonl") for name in members)
            has_blocked = any(name.endswith("generation_blocked_status.json") for name in members)
            shards_present = sorted(shard for shard in EXPECTED_SHARDS if shard in lowered)
            status_names = [name for name in members if name.endswith("generation_status.json")]
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
                if name.endswith((".json", ".jsonl")):
                    try:
                        loaded = json.loads(archive.read(name).decode("utf-8")) if name.endswith(".json") else None
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    claim_true = claim_true or has_claim_allowed_true(loaded)
            if has_blocked:
                blocker = "BLOCKED_GENERATED_MANIFEST_INVALID"
            elif claim_true or not has_manifest or set(shards_present) != EXPECTED_SHARDS:
                blocker = "BLOCKED_GENERATED_MANIFEST_INVALID"
            elif status.get("passed") is not True or status.get("status_code") != "VALIDATED_GENERATED_PILOT" or status.get("claim_allowed") is not False:
                blocker = "BLOCKED_GENERATED_MANIFEST_INVALID"
            else:
                blocker = None
            return {
                "status": "ready" if blocker is None else "blocked",
                "blocker_code": blocker,
                "member_count": len(members),
                "has_manifest": has_manifest,
                "has_blocked_status": has_blocked,
                "shards_present": shards_present,
                "status_code": status.get("status_code"),
                "next_status": "READY_FOR_FEATURE_INPUT_PACKAGE" if blocker is None else None,
                "claim_allowed": False,
                "evidence_status": "run_log_only",
            }
    except (OSError, zipfile.BadZipFile):
        return {
            "status": "blocked",
            "blocker_code": "BLOCKED_GENERATION_OUTPUT_CORRUPT",
            "claim_allowed": False,
            "evidence_status": "NO_REAL_EVIDENCE",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    parser.add_argument("--out-json", default="data/results/v7_generation_import_summary.json")
    args = parser.parse_args(argv)
    payload = inspect_generation_zip(args.zip)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ready" else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
