"""Frozen execution semantics layered on the immutable CIFAR 10k v2 study."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from certgen.icml2027.common import file_sha256, load_mapping, stable_hash
from certgen.icml2027.study_v2 import prospective_sample_ids


STUDY_ID = "icml2027_cifar_confirmatory_10k_v2"
STUDY_HASH = "0b77851744d8c6a506cc8530f7fc99a92aa0fefa198c1b64711e1924d944c176"
CONFIG_PATH = "configs/icml2027/cifar_confirmatory_10k_v2.yaml"
CONFIG_SHA256 = "7d543ddd077edeea20bf29d322916a8d0f531ff05787cb779dc2a35506e85e2d"
REFERENCE_PLAN_SHA256 = "f2ae231aa67b0f3b29995451ae56f7fa0a01b0e2410664022dd024a3cb47804e"
EXECUTION_CONTRACT_ID = "icml2027_cifar_confirmatory_10k_v2_execution_contract_v1"
SEED_DERIVATION = "certgen.icml2027.generator_rng.v1"
MODEL_CHECKPOINTS: dict[str, dict[str, str]] = {
    "google_ddpm_cifar10_candidate": {
        "checkpoint_id": "google/ddpm-cifar10-32",
        "checkpoint_revision": "267b167dc01f0e4e61923ea244e8b988f84deb80",
    },
    "frank_ddpm_ema_cifar10_candidate": {
        "checkpoint_id": "FrankCCCCC/ddpm_ema_cifar10",
        "checkpoint_revision": "6aa387f240fbb00d0e003f93a3b994f56dd98dc2",
    },
}

REQUIRED_WORKER_FIELDS = {
    "schema_version",
    "lane",
    "study_id",
    "study_hash",
    "configuration_sha256",
    "input_package_sha256",
    "model_revisions",
    "extractor_revisions",
    "preprocessing_hashes",
    "seed_plan_sha256",
    "sample_identity_policy_sha256",
    "expected_prefix_hashes",
    "expected_sample_count",
    "expected_shard_count",
    "expected_shard_coverage",
    "output_schema_version",
    "claim_allowed",
}


def derive_generator_seed(
    *, study_id: str, model_id: str, sample_id: str, master_seed: int
) -> int:
    """Derive a non-negative signed-64-bit seed from a domain-separated UTF-8 string."""

    values = (study_id, model_id, sample_id)
    if any(not value or "\x00" in value for value in values):
        raise ValueError("generator seed identity fields must be non-empty and NUL-free")
    canonical = "\x00".join((SEED_DERIVATION, *values, str(int(master_seed))))
    digest = hashlib.sha256(canonical.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False) & ((1 << 63) - 1)


def build_generator_seed_manifest(
    *,
    count_per_model: int = 10_000,
    master_seed: int = 20_270_812,
) -> dict[str, Any]:
    if count_per_model <= 0:
        raise ValueError("count_per_model must be positive")
    rows: list[dict[str, Any]] = []
    seen_seeds: set[int] = set()
    for model_id, checkpoint in MODEL_CHECKPOINTS.items():
        sample_ids = prospective_sample_ids(STUDY_ID, model_id, master_seed, count_per_model)
        for sample_index, sample_id in enumerate(sample_ids):
            generator_seed = derive_generator_seed(
                study_id=STUDY_ID,
                model_id=model_id,
                sample_id=sample_id,
                master_seed=master_seed,
            )
            if generator_seed in seen_seeds:
                raise RuntimeError("generator seed collision: freeze a new derivation version; never retry silently")
            seen_seeds.add(generator_seed)
            rows.append(
                {
                    "study_id": STUDY_ID,
                    "study_hash": STUDY_HASH,
                    "model_id": model_id,
                    **checkpoint,
                    "sample_index": sample_index,
                    "sample_id": sample_id,
                    "generator_seed": generator_seed,
                    "derivation": SEED_DERIVATION,
                    "claim_allowed": False,
                }
            )
    payload: dict[str, Any] = {
        "schema_version": "certgen.icml2027.generator_seed_manifest.v1",
        "study_id": STUDY_ID,
        "study_hash": STUDY_HASH,
        "count_per_model": count_per_model,
        "master_seed": master_seed,
        "derivation_contract": {
            "canonical_input": "domain\\0study_id\\0model_id\\0sample_id\\0master_seed_decimal",
            "hash": "SHA-256",
            "bytes": "first_8",
            "byte_order": "big",
            "integer_range": [0, (1 << 63) - 1],
            "collision_behavior": "hard_fail_and_version_derivation; no retry",
            "generator_api": "torch.Generator(device=device).manual_seed(generator_seed)",
        },
        "records": rows,
        "claim_allowed": False,
    }
    payload["manifest_sha256"] = stable_hash(payload)
    return payload


def validate_generator_seed_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    count = int(payload.get("count_per_model", 0))
    master_seed = int(payload.get("master_seed", -1))
    regenerated = build_generator_seed_manifest(count_per_model=count, master_seed=master_seed)
    if payload.get("manifest_sha256") != stable_hash({k: v for k, v in payload.items() if k != "manifest_sha256"}):
        errors.append("manifest self-hash mismatch")
    if dict(payload) != regenerated:
        errors.append("manifest does not exactly regenerate")
    rows = payload.get("records", [])
    if not isinstance(rows, list):
        errors.append("records must be a list")
        rows = []
    sample_ids = [str(row.get("sample_id", "")) for row in rows if isinstance(row, dict)]
    seeds = [int(row.get("generator_seed", -1)) for row in rows if isinstance(row, dict)]
    if len(sample_ids) != len(set(sample_ids)):
        errors.append("sample IDs are not globally unique")
    if len(seeds) != len(set(seeds)):
        errors.append("generator seeds are not globally unique")
    if any(sample_id == str(seed) for sample_id, seed in zip(sample_ids, seeds, strict=True)):
        errors.append("sample identity was conflated with generator seed")
    return {
        "passed": not errors,
        "errors": errors,
        "manifest_sha256": payload.get("manifest_sha256"),
        "records": len(rows),
        "claim_allowed": False,
    }


def seed_collision_audit(*, count: int = 100_000, master_seed: int = 20_270_812) -> dict[str, Any]:
    if count < 100_000:
        raise ValueError("closure collision audit requires at least 100,000 synthetic identities")
    seeds = [
        derive_generator_seed(
            study_id=STUDY_ID,
            model_id="collision_audit_model",
            sample_id=f"synthetic_sample_{index:08d}",
            master_seed=master_seed,
        )
        for index in range(count)
    ]
    collisions = count - len(set(seeds))
    return {"passed": collisions == 0, "identities": count, "collisions": collisions, "claim_allowed": False}


def build_execution_contract(seed_manifest: Mapping[str, Any], *, root: str | Path = ".") -> dict[str, Any]:
    workspace = Path(root)
    config = load_mapping(workspace / CONFIG_PATH)
    feature_registry = load_mapping(workspace / "registry/cvpr/feature_space_registry.yaml")
    if file_sha256(workspace / CONFIG_PATH) != CONFIG_SHA256:
        raise RuntimeError("immutable v2 study config changed")
    sample_policy = dict(config["sample_identity"])
    generator_policy = dict(seed_manifest["derivation_contract"])
    feature_rows = {
        str(row["feature_space_id"]): row
        for row in feature_registry["feature_spaces"]
        if row.get("feature_space_id") in {"inception", "clip"}
    }
    extractors = {
        extractor_id: {
            "model_identifier": row["model_identifier"],
            "revision": row["revision"],
            "preprocessing_sha256": stable_hash(row["expected_preprocessing"]),
            "dimension": row["expected_dimension"],
            "dtype": "float32",
        }
        for extractor_id, row in feature_rows.items()
    }
    payload: dict[str, Any] = {
        "schema_version": "certgen.icml2027.execution_contract.v1",
        "execution_contract_id": EXECUTION_CONTRACT_ID,
        "study_id": STUDY_ID,
        "study_hash": STUDY_HASH,
        "configuration_sha256": CONFIG_SHA256,
        "reference_plan_sha256": REFERENCE_PLAN_SHA256,
        "models": MODEL_CHECKPOINTS,
        "feature_spaces": ["inception", "clip"],
        "extractors": extractors,
        "expected_sample_count_per_model": 10_000,
        "expected_prefix_hashes": config["prefix_sample_id_hashes"],
        "sample_identity_policy": sample_policy,
        "sample_identity_policy_sha256": stable_hash(sample_policy),
        "generator_rng_policy": generator_policy,
        "generator_rng_policy_sha256": stable_hash(generator_policy),
        "seed_plan_sha256": stable_hash(config["seed_plan"]),
        "seed_manifest_sha256": seed_manifest["manifest_sha256"],
        "probability_space_interpretation": "unconditional_over_precommitted_iid_reference_draw_and_randomized_generator_seed_law",
        "realized_manifest_conditioning": "validity_claim_requires_the_randomized_design_law; conditional_replay_is_reproducibility_only",
        "output_schema_versions": {
            "generation": "certgen.icml2027.generation_payload.v1",
            "features": "certgen.icml2027.feature_payload.v1",
        },
        "claim_allowed": False,
    }
    payload["execution_contract_sha256"] = stable_hash(payload)
    return payload


def validate_worker_spec(
    spec: Mapping[str, Any],
    *,
    expected_lane: str,
    contract: Mapping[str, Any] | None,
) -> dict[str, Any]:
    errors = [f"missing field: {field}" for field in sorted(REQUIRED_WORKER_FIELDS - set(spec))]
    expected: dict[str, Any] = {"lane": expected_lane, "claim_allowed": False}
    if contract is not None:
        expected.update(
            {
                "study_id": contract["study_id"],
                "study_hash": contract["study_hash"],
                "configuration_sha256": contract["configuration_sha256"],
                "seed_plan_sha256": contract["seed_plan_sha256"],
                "sample_identity_policy_sha256": contract["sample_identity_policy_sha256"],
            }
        )
    for field, value in expected.items():
        if spec.get(field) != value:
            errors.append(f"scientific identity mismatch: {field}")
    for field in (
        "study_hash",
        "configuration_sha256",
        "input_package_sha256",
        "seed_plan_sha256",
        "sample_identity_policy_sha256",
    ):
        value = spec.get(field)
        if not isinstance(value, str) or len(value) != 64:
            errors.append(f"{field} must be an exact SHA-256")
    reference = spec.get("reference_plan_sha256")
    if reference is not None and (not isinstance(reference, str) or len(reference) != 64):
        errors.append("reference_plan_sha256 must be null or an exact SHA-256")
    if not isinstance(spec.get("study_id"), str) or not spec.get("study_id"):
        errors.append("study_id must be non-empty")
    for field in ("model_revisions", "extractor_revisions", "preprocessing_hashes"):
        if not isinstance(spec.get(field), dict):
            errors.append(f"{field} must be a mapping")
    if expected_lane == "cifar_10k_generation" and contract is not None and reference != REFERENCE_PLAN_SHA256:
        errors.append("scientific identity mismatch: reference_plan_sha256")
    if expected_lane == "dinov2_features" and (
        spec.get("robustness_feature_space") is not True or spec.get("confirmatory_family") is not False
    ):
        errors.append("DINO feature worker must remain robustness-only")
    return {"passed": not errors, "errors": errors, "claim_allowed": False}


def _job_indices(job: Mapping[str, Any]) -> range:
    start = int(job.get("sample_index_start", -1))
    stop = int(job.get("sample_index_stop", -1))
    if start < 0 or stop <= start:
        raise ValueError("invalid half-open sample-index coverage")
    return range(start, stop)


def validate_generation_job_partition(
    jobs: Sequence[Mapping[str, Any]],
    seed_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    expected_by_model: dict[str, set[int]] = {
        model_id: set(range(int(seed_manifest["count_per_model"]))) for model_id in MODEL_CHECKPOINTS
    }
    observed: dict[str, list[int]] = {model_id: [] for model_id in MODEL_CHECKPOINTS}
    for job in jobs:
        model_id = str(job.get("model_id", ""))
        if model_id not in observed:
            errors.append(f"wrong or extra model: {model_id}")
            continue
        try:
            indices = list(_job_indices(job))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        observed[model_id].extend(indices)
        rows = seed_manifest["records"]
        declared = job.get("seed_records_sha256")
        selected = [row for row in rows if row["model_id"] == model_id and row["sample_index"] in set(indices)]
        if declared != stable_hash(selected):
            errors.append(f"seed-record identity mismatch: {model_id}/{indices[0]}:{indices[-1] + 1}")
    for model_id, values in observed.items():
        counts = Counter(values)
        duplicates = sorted(index for index, value in counts.items() if value > 1)
        missing = sorted(expected_by_model[model_id] - set(values))
        extra = sorted(set(values) - expected_by_model[model_id])
        if duplicates:
            errors.append(f"overlap for {model_id}: {duplicates[:3]}")
        if missing:
            errors.append(f"gap for {model_id}: {missing[:3]}")
        if extra:
            errors.append(f"extra indices for {model_id}: {extra[:3]}")
    return {"passed": not errors, "errors": errors, "claim_allowed": False}


def validate_feature_job_partition(
    jobs: Sequence[Mapping[str, Any]],
    *,
    required_extractors: Sequence[str],
    required_roles: Sequence[str],
    expected_shards: int,
    source_sample_order_sha256: str,
) -> dict[str, Any]:
    errors: list[str] = []
    expected = {
        (extractor, role, shard)
        for extractor in required_extractors
        for role in required_roles
        for shard in range(expected_shards)
    }
    observed: list[tuple[str, str, int]] = []
    for job in jobs:
        key = (str(job.get("extractor_id", "")), str(job.get("source_role", "")), int(job.get("shard_id", -1)))
        observed.append(key)
        if int(job.get("num_shards", -1)) != expected_shards:
            errors.append(f"wrong shard count: {key}")
        if job.get("source_sample_order_sha256") != source_sample_order_sha256:
            errors.append(f"source sample order mismatch: {key}")
    counts = Counter(observed)
    for key in sorted(expected - set(observed)):
        errors.append(f"missing feature shard: {key}")
    for key in sorted(set(observed) - expected):
        errors.append(f"extra feature shard: {key}")
    for key, value in sorted(counts.items()):
        if value > 1:
            errors.append(f"duplicate feature shard: {key}")
    return {"passed": not errors, "errors": errors, "claim_allowed": False}


def build_generation_jobs(
    seed_manifest: Mapping[str, Any], *, shard_size: int = 500
) -> list[dict[str, Any]]:
    if shard_size <= 0 or int(seed_manifest["count_per_model"]) % shard_size:
        raise ValueError("shard_size must evenly divide the per-model sample count")
    jobs: list[dict[str, Any]] = []
    records = seed_manifest["records"]
    for model_id, checkpoint in MODEL_CHECKPOINTS.items():
        for start in range(0, int(seed_manifest["count_per_model"]), shard_size):
            stop = start + shard_size
            selected = [
                row
                for row in records
                if row["model_id"] == model_id and start <= int(row["sample_index"]) < stop
            ]
            jobs.append(
                {
                    "job_id": f"{model_id}_{start:05d}_{stop:05d}",
                    "model_id": model_id,
                    **checkpoint,
                    "sample_index_start": start,
                    "sample_index_stop": stop,
                    "sample_count": len(selected),
                    "seed_records_sha256": stable_hash(selected),
                    "device": "cuda",
                    "batch_size": 32,
                    "claim_allowed": False,
                }
            )
    validation = validate_generation_job_partition(jobs, seed_manifest)
    if not validation["passed"]:
        raise RuntimeError(f"generated job partition is invalid: {validation['errors']}")
    return jobs


def build_generation_worker_spec(
    seed_manifest: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    input_package_sha256: str,
    shard_size: int = 500,
) -> dict[str, Any]:
    if len(input_package_sha256) != 64:
        raise ValueError("input_package_sha256 must bind the authenticated prerequisite set")
    jobs = build_generation_jobs(seed_manifest, shard_size=shard_size)
    return {
        "schema_version": "certgen.icml2027.worker_spec.v1",
        "lane": "cifar_10k_generation",
        "study_id": contract["study_id"],
        "study_hash": contract["study_hash"],
        "configuration_sha256": contract["configuration_sha256"],
        "input_package_sha256": input_package_sha256,
        "reference_plan_sha256": contract["reference_plan_sha256"],
        "model_revisions": contract["models"],
        "extractor_revisions": {
            key: value["revision"] for key, value in contract["extractors"].items()
        },
        "preprocessing_hashes": {
            key: value["preprocessing_sha256"] for key, value in contract["extractors"].items()
        },
        "seed_plan_sha256": contract["seed_plan_sha256"],
        "sample_identity_policy_sha256": contract["sample_identity_policy_sha256"],
        "expected_prefix_hashes": contract["expected_prefix_hashes"],
        "expected_sample_count": int(seed_manifest["count_per_model"]) * len(MODEL_CHECKPOINTS),
        "expected_shard_count": len(jobs),
        "expected_shard_coverage": [job["job_id"] for job in jobs],
        "output_schema_version": contract["output_schema_versions"]["generation"],
        "jobs": jobs,
        "claim_allowed": False,
    }


def build_feature_jobs(
    *,
    source_sample_order_sha256: str,
    expected_shards: int = 20,
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    roles = ["reference", *MODEL_CHECKPOINTS]
    for extractor_id in ("inception", "clip"):
        for role in roles:
            for shard_id in range(expected_shards):
                jobs.append(
                    {
                        "job_id": f"{extractor_id}_{role}_{shard_id:03d}",
                        "extractor_id": extractor_id,
                        "source_role": role,
                        "shard_id": shard_id,
                        "num_shards": expected_shards,
                        "source_sample_order_sha256": source_sample_order_sha256,
                        "claim_allowed": False,
                    }
                )
    validation = validate_feature_job_partition(
        jobs,
        required_extractors=["inception", "clip"],
        required_roles=roles,
        expected_shards=expected_shards,
        source_sample_order_sha256=source_sample_order_sha256,
    )
    if not validation["passed"]:
        raise RuntimeError(f"generated feature partition is invalid: {validation['errors']}")
    return jobs
