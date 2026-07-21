# Prompt 03 — Feature and Metric Foundation

## Objective

Build the basic feature-cache and metric foundation for CertGen without requiring heavy vision dependencies or real datasets. V1 should support toy/smoke arrays and define the contracts for later real feature extraction.

## Required context

Read:

- `CERTGEN_PROJECT_MASTER_CONTEXT.md`
- `00_GLOBAL_RULES_FOR_ALL_PROMPTS.md`
- Prompt 01 and 02 outputs

## Feature cache contract

Implement `certgen/core/io.py` helpers for local arrays:

- save/load `.npz` feature arrays;
- record shape, dtype, path, hash;
- validate `num_items` and `feature_dim` against manifest;
- never silently accept mismatched shapes.

Implement a feature manifest creator:

```python
make_feature_manifest(
    dataset_or_model_id: str,
    feature_type: str,
    feature_path: str,
    preprocessing: dict,
    evidence_status: str,
) -> FeatureManifest
```

## Feature extraction placeholders

Create documentation and placeholder modules only. Do not make PyTorch mandatory.

Add:

```text
certgen/features/
  __init__.py
  extract_inception.py
  extract_clip.py
  extract_dinov2.py
```

Each module should:

- expose a CLI stub with `--dry-run`;
- clearly say heavy dependencies are optional;
- refuse to run real extraction unless dependencies and input paths are explicitly provided;
- write no evidence by default.

## Metric implementations

Implement CPU-safe metric functions for array inputs:

### MMD / KID-style core

In `certgen/metrics/mmd.py`:

- polynomial kernel;
- RBF kernel optional;
- unbiased MMD² estimator;
- batched or block contribution stream helper where possible.

In `certgen/metrics/kid.py`:

- KID wrapper using polynomial kernel MMD;
- fixed-n point estimate;
- optional block estimates.

In `certgen/metrics/cmmd.py`:

- CMMD wrapper as MMD over CLIP-like features;
- no actual CLIP dependency required; input arrays are enough.

### FID descriptive implementation

In `certgen/metrics/fid.py`:

- implement mean/covariance FID for feature arrays;
- use scipy `sqrtm` if available, otherwise fail with a clear dependency message;
- mark outputs as `descriptive_only` in V1;
- never expose `supports_clean_cs=True` for FID.

### FD-DINOv2 descriptive implementation

In `certgen/metrics/fd_dinov2.py`:

- reuse FID-style distance over DINOv2 features;
- descriptive only unless later certificate support is explicitly implemented.

## Metric registry

Create a registry mapping metric names to:

- metric family;
- required feature type;
- whether it supports clean CS;
- whether it is descriptive only;
- estimator callable.

Example:

```python
METRIC_REGISTRY = {
  "kid_poly": {"family": "kid", "supports_clean_cs": True, ...},
  "cmmd_poly": {"family": "cmmd", "supports_clean_cs": True, ...},
  "fid_inception": {"family": "fid", "supports_clean_cs": False, "fid_rigor_status": "descriptive_only", ...},
}
```

## Smoke metric CLI

Add:

```bash
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics
```

It should compute toy KID/CMMD/FID descriptive outputs on tiny generated arrays, but every output must be non-evidence.

## Tests

Add tests that:

1. MMD returns approximately zero when comparing identical arrays;
2. MMD is positive for clearly shifted toy distributions;
3. KID wrapper calls MMD logic correctly;
4. CMMD wrapper works on arbitrary feature arrays;
5. FID returns zero-ish for identical arrays;
6. FID metric record is always `descriptive_only` and `supports_clean_cs=False`;
7. feature manifest rejects shape mismatch;
8. all metric smoke outputs are non-evidence.

## Acceptance criteria

Run:

```bash
python -m pytest -q
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics
```

Then write `docs/V1_METRICS_FOUNDATION_REPORT.md` with limitations clearly stated.
