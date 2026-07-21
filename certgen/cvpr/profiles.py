"""Immutable prospective pilot profiles for the canonical CVPR pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import stable_hash_json


PROFILE_SCHEMA = "certgen.cvpr.pilot_profile.v1"
DEFAULT_PROFILE_ROOT = Path("configs/cvpr/profiles")
REQUIRED_FIELDS = {
    "schema_version",
    "profile_id",
    "purpose",
    "benchmark",
    "models",
    "extractors",
    "generation_count",
    "reference_count",
    "sample_budgets",
    "feature_spaces",
    "metrics",
    "comparison_family",
    "comparisons",
    "controls",
    "controls_in_confirmatory_family",
    "controls_claim_allowed",
    "evidence_class",
    "claim_allowed",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"pilot profile must be a mapping: {path}")
    return payload


def validate_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    errors = [f"missing field: {name}" for name in sorted(REQUIRED_FIELDS - set(profile))]
    if profile.get("schema_version") != PROFILE_SCHEMA:
        errors.append(f"schema_version must be {PROFILE_SCHEMA}")
    profile_id = str(profile.get("profile_id", ""))
    if not profile_id or not profile_id.replace("_", "").isalnum():
        errors.append("profile_id must be a path-safe identifier")
    if profile.get("benchmark") != "cifar10":
        errors.append("the canonical pilot profiles currently require benchmark=cifar10")
    for field in (
        "models",
        "extractors",
        "sample_budgets",
        "feature_spaces",
        "metrics",
        "comparisons",
        "controls",
    ):
        value = profile.get(field)
        if not isinstance(value, list) or not value:
            errors.append(f"{field} must be a non-empty prospective list")
        elif len({str(item) for item in value}) != len(value):
            errors.append(f"{field} must not contain duplicates")
    if profile.get("extractors") != profile.get("feature_spaces"):
        errors.append("extractors and feature_spaces must have identical frozen order")
    comparisons = set(map(str, profile.get("comparisons", [])))
    controls = set(map(str, profile.get("controls", [])))
    if comparisons & controls:
        errors.append("sanity controls must not appear in the confirmatory comparisons")
    if profile.get("controls_in_confirmatory_family") is not False:
        errors.append("controls_in_confirmatory_family must be false")
    if profile.get("controls_claim_allowed") is not False:
        errors.append("controls_claim_allowed must be false")
    for field in ("generation_count", "reference_count"):
        value = profile.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"{field} must be a positive integer")
    budgets = profile.get("sample_budgets")
    if isinstance(budgets, list) and any(
        not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in budgets
    ):
        errors.append("sample_budgets must contain positive integers")
    if profile.get("claim_allowed") is not False:
        errors.append("pilot profiles must set claim_allowed=false")
    if profile.get("evidence_class") != "pilot_only":
        errors.append("pre-run pilot profiles must use evidence_class=pilot_only")
    declared = profile.get("profile_hash")
    computed = stable_hash_json({key: value for key, value in profile.items() if key != "profile_hash"})
    if declared is not None and declared != computed:
        errors.append("profile_hash mismatch")
    return {
        "passed": not errors,
        "profile_id": profile_id or None,
        "profile_hash": computed,
        "errors": errors,
        "claim_allowed": False,
    }


def freeze_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(profile)
    payload.pop("profile_hash", None)
    verdict = validate_profile(payload)
    if not verdict["passed"]:
        raise ValueError("invalid pilot profile: " + "; ".join(verdict["errors"]))
    payload["profile_hash"] = verdict["profile_hash"]
    return payload


def list_profiles(profile_root: str | Path = DEFAULT_PROFILE_ROOT) -> list[dict[str, Any]]:
    root = Path(profile_root)
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.yaml")):
        profile = freeze_profile(_load_yaml(path))
        rows.append(
            {
                "profile_id": profile["profile_id"],
                "purpose": profile["purpose"],
                "models": profile["models"],
                "extractors": profile["extractors"],
                "generation_count": profile["generation_count"],
                "reference_count": profile["reference_count"],
                "evidence_class": profile["evidence_class"],
                "claim_allowed": False,
                "profile_hash": profile["profile_hash"],
            }
        )
    if not rows:
        raise FileNotFoundError(f"no pilot profiles found under {root}")
    return rows


def load_profile(profile_id: str, profile_root: str | Path = DEFAULT_PROFILE_ROOT) -> dict[str, Any]:
    if not profile_id or not profile_id.replace("_", "").isalnum():
        raise ValueError("profile_id must be path-safe")
    path = Path(profile_root) / f"{profile_id}.yaml"
    if not path.is_file():
        available = [row["profile_id"] for row in list_profiles(profile_root)]
        raise KeyError(f"unknown pilot profile {profile_id!r}; available={available}")
    profile = freeze_profile(_load_yaml(path))
    if profile["profile_id"] != profile_id:
        raise ValueError("profile filename and profile_id disagree")
    return profile


def load_profile_path(path: str | Path) -> dict[str, Any]:
    """Load a fixture or externally supplied prospective profile by explicit path."""

    return freeze_profile(_load_yaml(Path(path)))


def resolve_selection(
    *,
    profile: Mapping[str, Any] | None,
    models: list[str] | None,
    extractors: list[str] | None,
) -> tuple[list[str], list[str], dict[str, Any] | None]:
    """Resolve one prospective selection without outcome-dependent fallback."""

    if profile is not None and (models is not None or extractors is not None):
        raise ValueError("--profile cannot be combined with explicit --models/--extractors")
    if profile is not None:
        frozen = freeze_profile(profile)
        return list(frozen["models"]), list(frozen["extractors"]), frozen
    if models is None and extractors is None:
        return [], [], None
    if not models or not extractors:
        raise ValueError("explicit selection requires both non-empty --models and --extractors")
    if len(set(models)) != len(models) or len(set(extractors)) != len(extractors):
        raise ValueError("explicit selection contains duplicates")
    return list(models), list(extractors), None
