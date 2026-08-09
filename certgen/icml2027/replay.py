"""Deterministic CPU replay for registered ICML 2027 study derivations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from certgen.icml2027.common import file_sha256, load_mapping, stable_hash, write_json
from certgen.icml2027.synthetic.engine import run_synthetic_suite


def _find_study(registry: dict[str, Any], study_id: str) -> dict[str, Any]:
    for study in registry.get("studies", []):
        if study.get("study_id") == study_id:
            return study
    raise ValueError(f"study not found in registry: {study_id}")


def replay_study(
    study_id: str,
    *,
    registry_path: str | Path = "registry/icml2027/study_registry.yaml",
    out_dir: str | Path = "artifacts/icml2027/replay",
) -> dict[str, Any]:
    registry = load_mapping(registry_path)
    study = _find_study(registry, study_id)
    if study.get("claim_allowed") is not False:
        raise ValueError("registered study must set claim_allowed=false")
    inputs = study.get("authenticated_inputs", [])
    errors: list[str] = []
    for item in inputs:
        path = Path(str(item["path"]))
        if not path.is_file():
            errors.append(f"missing authenticated input: {path}")
        elif item.get("sha256") and item["sha256"] != file_sha256(path):
            errors.append(f"authenticated input hash mismatch: {path}")
    target = Path(out_dir) / study_id
    derivation = study.get("replay_derivation")
    replay_output: dict[str, Any] | None = None
    if not errors and derivation == "synthetic_suite":
        config_path = Path(str(study["config_path"]))
        if study.get("config_sha256") and study["config_sha256"] != file_sha256(config_path):
            errors.append("synthetic replay config hash mismatch")
        else:
            replay_config = load_mapping(config_path)
            replay_config["report_root"] = str(target / "reports")
            target.mkdir(parents=True, exist_ok=True)
            replay_config_path = target / "authenticated_replay_config.yaml"
            replay_config_path.write_text(yaml.safe_dump(replay_config, sort_keys=False), encoding="utf-8")
            replay_output = run_synthetic_suite(replay_config_path, target / "synthetic")
    elif not errors and derivation not in {None, "planning_only"}:
        errors.append(f"unsupported replay derivation: {derivation}")
    payload = {
        "schema_version": "certgen.icml2027.replay_result.v1",
        "study_id": study_id,
        "study_contract_hash": stable_hash(study),
        "authenticated_inputs_verified": not errors,
        "derivation": derivation,
        "replay_output": replay_output,
        "errors": errors,
        "passed": not errors,
        "synthetic_validation_only": derivation == "synthetic_suite",
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
    write_json(target / "replay_result.json", payload)
    return payload
