from __future__ import annotations

import json
import zipfile
from pathlib import Path

from certgen.packaging.import_kaggle_feature_outputs import inspect_feature_zip
from certgen.packaging.import_kaggle_generation_outputs import inspect_generation_zip


def test_generation_import_missing_zip() -> None:
    payload = inspect_generation_zip("does-not-exist.zip")
    assert payload["blocker_code"] == "BLOCKED_GENERATION_OUTPUT_ZIP_MISSING"
    assert payload["claim_allowed"] is False


def test_generation_import_valid_fake_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "generation.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for shard in ["google_ddpm_gpu0", "google_ddpm_gpu1", "frank_ddpm_ema_gpu0", "frank_ddpm_ema_gpu1", "frank_cfm_gpu0", "frank_cfm_gpu1"]:
            archive.writestr(f"manifests/{shard}.jsonl", "")
        archive.writestr(
            "status/generation_status.json",
            json.dumps({"passed": True, "status_code": "VALIDATED_GENERATED_PILOT", "claim_allowed": False}),
        )
    payload = inspect_generation_zip(zip_path)
    assert payload["status"] == "ready"
    assert payload["next_status"] == "READY_FOR_FEATURE_INPUT_PACKAGE"


def test_feature_import_missing_roles_blocked(tmp_path: Path) -> None:
    zip_path = tmp_path / "features.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("reference/inception/features.json", "{}")
    payload = inspect_feature_zip(zip_path)
    assert payload["blocker_code"] == "BLOCKED_FEATURE_CACHE_INVALID"


def test_feature_import_valid_fake_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "features.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for role in ["reference", "google_ddpm", "frank_ddpm_ema", "frank_cfm"]:
            for family in ["inception", "clip"]:
                archive.writestr(f"split/{role}_{family}.npz", b"fixture")
                archive.writestr(f"split/{role}_{family}.sidecar.json", json.dumps({"claim_allowed": False}))
        archive.writestr(
            "status/feature_extraction_status.json",
            json.dumps({"status_code": "FEATURE_EXTRACTION_SHARDS_COMPLETE", "claim_allowed": False}),
        )
    payload = inspect_feature_zip(zip_path)
    assert payload["status"] == "ready"
    assert payload["next_status"] == "READY_FOR_METRIC_SANITY_GATES"
