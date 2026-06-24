import numpy as np

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.pilot.orchestrator import run_first_pilot


def _cache(tmp_path, name, arr):
    npz = tmp_path / f"{name}.npz"
    np.savez_compressed(npz, features=arr, sample_ids=np.arange(len(arr)), source_paths=np.array([str(i) for i in range(len(arr))]))
    sidecar = tmp_path / f"{name}.json"
    write_json(
        {
            "cache_id": name,
            "benchmark_id": "bench",
            "model_id": name,
            "split": "test",
            "feature_extractor": "custom",
            "feature_dim": arr.shape[1],
            "n_samples": arr.shape[0],
            "preprocessing": {"resize": "none", "interpolation": "none", "crop": "none", "normalization": "none"},
            "source": {"type": "precomputed_features", "uri_or_path": str(npz), "license_status": "verified_free"},
            "hashes": {"features_sha256": file_sha256(npz), "source_manifest_sha256": "smoke"},
            "created_by": "test",
            "created_at": "2026-06-23",
            "certgen_version": "0.3.0",
        },
        sidecar,
    )
    return npz, sidecar


def test_first_pilot_dry_run_and_real_features(tmp_path):
    dry_cfg = tmp_path / "dry.yaml"
    dry_cfg.write_text("pilot_id: dry\nmode: dry_run\ncomparisons:\n  - comparison_id: c1\n", encoding="utf-8")
    dry = run_first_pilot(dry_cfg, tmp_path / "dry_out", tmp_path / "dry.md", tmp_path / "dry.json")
    assert dry["evidence_status"] == "dry_run_only"
    assert dry["claim_allowed"] is False

    ref_npz, ref_json = _cache(tmp_path, "ref", np.zeros((80, 2)) + np.linspace(0, 1, 160).reshape(80, 2))
    a_npz, a_json = _cache(tmp_path, "a", np.zeros((80, 2)) + np.linspace(0, 1, 160).reshape(80, 2) + 0.01)
    b_npz, b_json = _cache(tmp_path, "b", np.ones((80, 2)))
    repro = tmp_path / "metric_reproduction.json"
    write_json({"within_tolerance": True, "claim_allowed": False, "reproduction_status": "within_tolerance"}, repro)
    real_cfg = tmp_path / "real.yaml"
    real_cfg.write_text(
        f"""pilot_id: real
mode: real_features
metrics: [mmd_rbf, fid]
max_samples: 20
metric_reproduction_audit: {repro}
reference_cache:
  npz: {ref_npz}
  sidecar: {ref_json}
comparisons:
  - comparison_id: c1
    model_a_cache:
      npz: {a_npz}
      sidecar: {a_json}
    model_b_cache:
      npz: {b_npz}
      sidecar: {b_json}
""",
        encoding="utf-8",
    )
    real = run_first_pilot(real_cfg, tmp_path / "real_out", tmp_path / "real.md", tmp_path / "real.json")
    assert real["pilot_result_computed"] is True
    assert real["paper_claim_allowed"] is False
    assert any(item.get("status") == "descriptive_only" for item in real["certificates"])
