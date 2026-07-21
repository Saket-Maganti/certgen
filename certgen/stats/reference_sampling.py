"""Precommitted IID-with-replacement draw plans for finite reference pools.

The statistical target is the empirical distribution that puts mass 1/N on
each row of a fixed reference cache.  A deterministic seed fixes the complete
draw plan before any certificate value is inspected.  The resulting source
indices are IID under the declared pseudo-randomization law; repeated source
rows are allowed and expected.  These artifacts are protocol records, never
model evidence.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from certgen.core.hashing import stable_hash_json


SCHEMA_VERSION = "certgen.reference_draw_plan.v1"
SAMPLING_SCHEME = "iid_with_replacement_from_fixed_empirical_population"


def _normalise_source_ids(source_ids: Sequence[Any]) -> list[str]:
    ids = [str(item) for item in source_ids]
    if not ids:
        raise ValueError("reference population must contain at least one source ID")
    if any(not item for item in ids):
        raise ValueError("reference source IDs must be non-empty")
    if len(ids) != len(set(ids)):
        raise ValueError("reference population source IDs must be unique")
    return ids


def build_reference_draw_plan(
    source_ids: Sequence[Any],
    *,
    num_draws: int,
    seed: int,
    population_id: str,
    source_manifest_sha256: str,
) -> dict[str, Any]:
    """Build a deterministic, precommittable with-replacement draw plan."""

    ids = _normalise_source_ids(source_ids)
    if isinstance(num_draws, bool) or int(num_draws) != num_draws or int(num_draws) <= 0:
        raise ValueError("num_draws must be a positive integer")
    if isinstance(seed, bool) or int(seed) != seed or int(seed) < 0:
        raise ValueError("seed must be a nonnegative integer")
    if not str(population_id).strip():
        raise ValueError("population_id is required")
    if len(str(source_manifest_sha256)) != 64:
        raise ValueError("source_manifest_sha256 must be a 64-character SHA-256 hex digest")
    try:
        int(str(source_manifest_sha256), 16)
    except ValueError as exc:
        raise ValueError("source_manifest_sha256 must be hexadecimal") from exc

    rng = np.random.Generator(np.random.PCG64(int(seed)))
    source_indices = rng.integers(0, len(ids), size=int(num_draws), endpoint=False).astype(int).tolist()
    draws = [
        {
            "draw_id": f"reference_draw_{index:08d}",
            "draw_index": index,
            "source_index": source_index,
            "source_id": ids[source_index],
        }
        for index, source_index in enumerate(source_indices)
    ]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "sampling_scheme": SAMPLING_SCHEME,
        "target_population": "fixed_empirical_reference_distribution",
        "population_id": str(population_id),
        "population_size": len(ids),
        "source_ids_sha256": stable_hash_json(ids),
        "source_manifest_sha256": str(source_manifest_sha256),
        "num_draws": int(num_draws),
        "seed": int(seed),
        "rng_algorithm": "numpy.PCG64",
        "draws": draws,
        "draws_sha256": stable_hash_json(draws),
        "precommitment_required_before_stream": True,
        "evidence_status": "design_contract_only",
        "synthetic_validation_only": True,
        "not_model_evidence": True,
        "claim_allowed": False,
    }
    payload["plan_sha256"] = stable_hash_json(payload)
    return payload


def validate_reference_draw_plan(
    plan: dict[str, Any],
    *,
    source_ids: Sequence[Any] | None = None,
    min_draws: int | None = None,
) -> dict[str, Any]:
    """Fail closed unless ``plan`` exactly regenerates as IID-with-replacement."""

    errors: list[str] = []
    if plan.get("schema_version") != SCHEMA_VERSION:
        errors.append("reference draw-plan schema_version is unsupported")
    if plan.get("sampling_scheme") != SAMPLING_SCHEME:
        errors.append("reference sampling must be explicitly IID with replacement")
    if plan.get("target_population") != "fixed_empirical_reference_distribution":
        errors.append("reference target population must be the fixed empirical distribution")
    if plan.get("rng_algorithm") != "numpy.PCG64":
        errors.append("reference draw plan must lock rng_algorithm=numpy.PCG64")
    if plan.get("claim_allowed") is not False:
        errors.append("reference draw plan must set claim_allowed=false")
    draws = plan.get("draws")
    if not isinstance(draws, list) or not draws:
        errors.append("reference draw plan must contain non-empty draws")
        draws = []
    if plan.get("num_draws") != len(draws):
        errors.append("num_draws does not match draw records")
    if min_draws is not None and len(draws) < int(min_draws):
        errors.append(f"reference draw plan has fewer than required {int(min_draws)} draws")
    if plan.get("draws_sha256") != stable_hash_json(draws):
        errors.append("draws_sha256 mismatch")
    # A canonical CVPR wrapper may add an outer configuration hash.  That
    # metadata must not retroactively change the sampling plan's own digest.
    without_plan_hash = {
        key: value for key, value in plan.items() if key not in {"plan_sha256", "configuration_hash"}
    }
    if plan.get("plan_sha256") != stable_hash_json(without_plan_hash):
        errors.append("plan_sha256 mismatch")

    ids: list[str] | None = None
    if source_ids is not None:
        try:
            ids = _normalise_source_ids(source_ids)
        except ValueError as exc:
            errors.append(str(exc))
        if ids is not None:
            if plan.get("population_size") != len(ids):
                errors.append("population_size does not match source cache")
            if plan.get("source_ids_sha256") != stable_hash_json(ids):
                errors.append("source_ids_sha256 does not match source cache order")

    population_size = 0
    seed = -1
    num_draws = 0
    population_value = plan.get("population_size")
    seed_value = plan.get("seed")
    num_draws_value = plan.get("num_draws")
    if (
        isinstance(population_value, int)
        and not isinstance(population_value, bool)
        and isinstance(seed_value, int)
        and not isinstance(seed_value, bool)
        and isinstance(num_draws_value, int)
        and not isinstance(num_draws_value, bool)
    ):
        population_size = population_value
        seed = seed_value
        num_draws = num_draws_value
    if population_size > 0 and seed >= 0 and num_draws > 0:
        regenerated = np.random.Generator(np.random.PCG64(seed)).integers(
            0, population_size, size=num_draws, endpoint=False
        ).astype(int).tolist()
    else:
        errors.append("population_size, seed, and num_draws must be valid positive integers")
        regenerated = []

    observed_indices: list[int] = []
    draw_ids: list[str] = []
    for index, row in enumerate(draws):
        if not isinstance(row, dict):
            errors.append(f"draw {index} is not an object")
            continue
        draw_ids.append(str(row.get("draw_id", "")))
        if row.get("draw_index") != index:
            errors.append(f"draw {index} has a noncanonical draw_index")
        source_index_value = row.get("source_index")
        if not isinstance(source_index_value, int) or isinstance(source_index_value, bool):
            errors.append(f"draw {index} has an invalid source_index")
            continue
        source_index = source_index_value
        observed_indices.append(source_index)
        if not 0 <= source_index < max(1, population_size):
            errors.append(f"draw {index} source_index is outside the population")
        if ids is not None and 0 <= source_index < len(ids) and row.get("source_id") != ids[source_index]:
            errors.append(f"draw {index} source_id does not match source_index")
    if len(draw_ids) != len(set(draw_ids)) or any(not item for item in draw_ids):
        errors.append("draw IDs must be unique and non-empty")
    if observed_indices != regenerated:
        errors.append("draw indices do not match deterministic with-replacement regeneration")

    return {
        "passed": not errors,
        "errors": errors,
        "schema_version": plan.get("schema_version"),
        "sampling_scheme": plan.get("sampling_scheme"),
        "plan_sha256": plan.get("plan_sha256"),
        "num_draws": len(draws),
        "num_unique_source_rows": len(set(observed_indices)),
        "claim_allowed": False,
        "evidence_status": "design_contract_only",
    }


def materialize_reference_draws(
    features: np.ndarray,
    source_ids: Sequence[Any],
    plan: dict[str, Any],
    *,
    min_draws: int | None = None,
) -> tuple[np.ndarray, list[str], dict[str, Any]]:
    """Materialize plan-ordered feature draws after full validation."""

    array = np.asarray(features)
    ids = _normalise_source_ids(source_ids)
    if array.ndim != 2 or len(array) != len(ids):
        raise ValueError("reference features and source IDs must have matching positive row counts")
    result = validate_reference_draw_plan(plan, source_ids=ids, min_draws=min_draws)
    if not result["passed"]:
        raise ValueError("invalid reference draw plan: " + "; ".join(result["errors"]))
    indices = np.asarray([int(row["source_index"]) for row in plan["draws"]], dtype=int)
    draw_ids = [str(row["draw_id"]) for row in plan["draws"]]
    return array[indices], draw_ids, result
