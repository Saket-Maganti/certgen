import json
from pathlib import Path

import numpy as np

from certgen.core.hashing import file_sha256
from certgen.features.cache_validate import validate_v3_feature_cache
from certgen.features.split_by_role import split_feature_cache_by_role
from certgen.pipeline.v6_execution import run_r1d_metric_reproduction_gate, run_r1e_first_pilot_audit


PREPROCESSING = {
    "image_size": 32,
    "resize_policy": "fixed_32",
    "interpolation": "bilinear",
    "crop": "none",
    "normalization": "inception",
}


def _write_split_cache(root: Path, role: str, extractor_label: str, features: np.ndarray) -> None:
    npz = root / "split" / f"{role}_{extractor_label}.npz"
    sidecar = root / "split" / f"{role}_{extractor_label}.sidecar.json"
    npz.parent.mkdir(parents=True, exist_ok=True)
    sample_ids = np.asarray([f"{role}_{idx:04d}" for idx in range(features.shape[0])])
    np.savez_compressed(npz, features=features.astype(np.float32), sample_ids=sample_ids)
    payload = {
        "extractor": "inception_v3_pool3" if extractor_label == "inception" else "clip_vit",
        "feature_extractor": "inception_v3_pool3" if extractor_label == "inception" else "clip_vit",
        "feature_dim": int(features.shape[1]),
        "n_samples": int(features.shape[0]),
        "num_items": int(features.shape[0]),
        "sample_ids": sample_ids.tolist(),
        "feature_path": str(npz),
        "features_sha256": file_sha256(npz),
        "hash": file_sha256(npz),
        "preprocessing": PREPROCESSING,
        "source": {"license_status": "allowed"},
        "hashes": {"features_sha256": file_sha256(npz), "source_manifest_sha256": "fixture", "preprocessing_lock_sha256": "fixture"},
        "created_by": "test_v6_execution_gates",
        "evidence_status": "real_features_unvalidated",
        "claim_allowed": False,
    }
    sidecar.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_split_feature_cache_by_role_outputs_valid_sidecars(tmp_path):
    features = np.arange(24, dtype=np.float32).reshape(6, 4)
    sample_ids = np.asarray([f"s{idx}" for idx in range(6)])
    merged = tmp_path / "merged.npz"
    sidecar = tmp_path / "merged.sidecar.json"
    manifest = tmp_path / "manifest.jsonl"
    np.savez_compressed(merged, features=features, sample_ids=sample_ids)
    sidecar.write_text(
        json.dumps(
            {
                "extractor": "inception_v3_pool3",
                "feature_dim": 4,
                "n_samples": 6,
                "sample_ids": sample_ids.tolist(),
                "preprocessing": PREPROCESSING,
                "source": {"license_status": "allowed"},
                "hashes": {"source_manifest_sha256": "fixture", "preprocessing_lock_sha256": "fixture"},
                "claim_allowed": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    rows = [{"sample_id": f"s{idx}", "role": "reference" if idx < 3 else "google_ddpm", "path": f"sample_{idx}.png"} for idx in range(6)]
    manifest.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    summary = split_feature_cache_by_role(
        features_npz=merged,
        sidecar=sidecar,
        sample_manifest=manifest,
        extractor_label="inception",
        out_dir=tmp_path / "split",
    )

    assert summary["claim_allowed"] is False
    result = validate_v3_feature_cache(
        features_path=tmp_path / "split" / "reference_inception.npz",
        sidecar_path=tmp_path / "split" / "reference_inception.sidecar.json",
        metric="mmd_rbf",
        strict_hash=True,
        allow_constant=True,
    )
    assert result.passed, result.errors


def test_r1d_blocks_cleanly_when_feature_caches_are_missing(tmp_path):
    payload = run_r1d_metric_reproduction_gate(
        feature_dir=tmp_path / "missing_features",
        out_json=tmp_path / "r1d.json",
        report=tmp_path / "r1d.md",
    )
    assert payload["status_code"] == "BLOCKED_FEATURE_EXTRACTION_NOT_RUN"
    assert payload["claim_allowed"] is False
    assert payload["within_tolerance"] is False


def test_r1e_blocks_cache_sanity_from_being_promoted_to_metric_reproduction(tmp_path):
    rng = np.random.default_rng(7)
    reference = rng.normal(size=(24, 6)).astype(np.float32)
    roles = {
        "reference": reference,
        "google_ddpm": reference + 0.05,
        "frank_ddpm_ema": reference + 0.10,
        "frank_cfm": reference + 0.75,
    }
    for extractor_label in ["inception", "clip"]:
        for role, features in roles.items():
            _write_split_cache(tmp_path, role, extractor_label, features)

    audit = run_r1e_first_pilot_audit(
        feature_dir=tmp_path,
        out=tmp_path / "r1e_audit.md",
        json_out=tmp_path / "r1e_audit.json",
        r1d_out_json=tmp_path / "r1d.json",
        r1d_report=tmp_path / "r1d.md",
        pilot_report=tmp_path / "r1e_report.md",
        fraction_json=tmp_path / "r1e_fraction.json",
        cert_dir=tmp_path / "certificates",
        feature_split_dir=tmp_path / "feature_splits",
    )

    assert audit["passed"], audit["blockers"]
    assert audit["pilot_status"] == "BLOCKED_R1D_NOT_READY"
    assert audit["claim_allowed"] is False
    assert audit["certificates"] == []
    r1d = json.loads((tmp_path / "r1d.json").read_text(encoding="utf-8"))
    assert r1d["status_code"] == "READY_FOR_METRIC_REPRODUCTION"
    assert r1d["cache_sanity_passed"] is True
    assert r1d["within_tolerance"] is False
    fraction = json.loads((tmp_path / "r1e_fraction.json").read_text(encoding="utf-8"))
    assert fraction["undecided_fraction"] is None
