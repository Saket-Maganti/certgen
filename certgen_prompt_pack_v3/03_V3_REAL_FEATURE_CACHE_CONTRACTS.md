# Prompt 03 — Real Feature-Cache Contracts

Upgrade feature-cache validation so real feature caches become auditable evidence candidates.

## Goal

V2 had a feature-cache schema/validator. V3 should make it strict enough for real pilot use.

Create/upgrade:

- `certgen/features/cache_contracts.py`
- `certgen/features/cache_validate.py`
- `certgen/cli/validate_feature_cache.py`
- `docs/FEATURE_CACHE_CONTRACT_V3.md`

## Feature cache format

Support `.npz` and JSON sidecar.

Expected `.npz` arrays:

- `features`: shape `(n, d)`, float32/float64
- optional `sample_ids`: shape `(n,)`
- optional `labels`: shape `(n,)`
- optional `source_paths`: shape `(n,)`

Expected sidecar:

```json
{
  "cache_id": "...",
  "benchmark_id": "...",
  "model_id": "...",
  "split": "...",
  "feature_extractor": "inception_v3_pool3|clip_vit|dinov2|custom",
  "feature_dim": 2048,
  "n_samples": 10000,
  "preprocessing": {
    "resize": 299,
    "interpolation": "bicubic",
    "crop": "center|none|custom",
    "normalization": "inception|clip|dinov2|custom"
  },
  "source": {
    "type": "released_samples|public_dataset|precomputed_features",
    "uri_or_path": "...",
    "license_status": "verified_free|unknown|restricted|not_allowed"
  },
  "hashes": {
    "features_sha256": "...",
    "source_manifest_sha256": "..."
  },
  "created_by": "...",
  "created_at": "...",
  "certgen_version": "..."
}
```

## Validation rules

Fail if:
- `n_samples` mismatches array rows;
- `feature_dim` mismatches array columns;
- feature values contain NaN/Inf;
- features are all constant or near-zero unless explicitly allowed;
- source license restricted/not allowed;
- feature extractor incompatible with requested metric;
- preprocessing_id missing;
- hashes mismatch when `--strict-hash` is used.

Warn if:
- sample_ids absent;
- source_paths absent;
- license unknown;
- created_by absent;
- source manifest hash absent;
- feature dtype is float64 and cache is large.

## CLI

```bash
python3 -m certgen.cli.validate_feature_cache \
  --features path/to/features.npz \
  --sidecar path/to/features.json \
  --out docs/FEATURE_CACHE_VALIDATION.md \
  --json-out data/results/feature_cache_validation.json \
  --strict-hash
```

## Evidence behavior

If validation passes:

```json
"evidence_status": "real_features_validated",
"claim_allowed": false
```

Validated features are not enough to allow claims. They only unlock pilot execution.

## Tests

Add temp `.npz` fixtures:
- valid cache;
- shape mismatch;
- NaN features;
- all-zero features;
- sidecar mismatch;
- restricted license;
- missing optional fields warning.

## Docs

Document exact cache contract and how to create a sidecar manually.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```
