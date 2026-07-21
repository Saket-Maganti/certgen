# CertGen Feature Cache Schema V2

Status: `IMPLEMENTED_LOCAL_CONTRACT_NOT_EXECUTED_ON_REAL_CACHE`

Evidence boundary: `synthetic_validation_only`, `not_model_evidence`, `claim_allowed=false`.

This document defines the next canonical cache contract. It does not migrate or validate any existing real cache. Historical files must remain untouched; migration writes a new sidecar next to the old artifact and never promotes evidence status automatically.

## Why a new canonical contract is necessary

The repository currently has three metadata dialects:

1. `certgen.features.cache_schema.FeatureCacheManifest`, a flat V2-style manifest;
2. `certgen.schemas.feature_manifest.FeatureManifest`, a smaller generic manifest;
3. loose extractor/V3 sidecars consumed through fallback aliases such as `extractor`, `feature_extractor`, `num_items`, `n_samples`, `hash`, and `features_sha256`.

None carries a required feature-cache schema version. The extractor, merge, split, validator, and importer therefore disagree on names and required provenance. `certgen.feature_cache.v2` replaces those dialects for new caches while preserving read-only compatibility with old artifacts.

## Canonical shape

```json
{
  "schema_version": "certgen.feature_cache.v2",
  "cache_id": "<stable id>",
  "role": "<reference or model role>",
  "benchmark": {
    "dataset_id": "<dataset id>",
    "split": "<split>",
    "source_manifest_path": "<portable relative path>",
    "source_manifest_sha256": "<sha256>"
  },
  "producer": {
    "model_or_generator_id": "<id>",
    "checkpoint_or_revision": "<resolved revision>",
    "checkpoint_sha256": null
  },
  "extractor": {
    "name": "<adapter name>",
    "resolved_model_id": "<resolved weights id>",
    "resolved_revision": "<immutable revision when available>",
    "checkpoint_sha256": null,
    "package_versions": {},
    "output_layer": "<layer>",
    "feature_dim": 0
  },
  "preprocessing": {
    "lock_id": "<lock id>",
    "lock_sha256": "<sha256>",
    "resize": "<explicit>",
    "interpolation": "<explicit>",
    "crop": "<explicit>",
    "color_mode": "rgb",
    "pixel_range": "<explicit>",
    "normalization": "<explicit>",
    "feature_normalization": "<none or l2>"
  },
  "array": {
    "path": "<portable relative path>",
    "sha256": "<sha256>",
    "dtype": "float32",
    "shape": [0, 0],
    "features_key": "features",
    "sample_ids_key": "sample_ids",
    "ordered_sample_ids_sha256": "<sha256>"
  },
  "shard": {
    "shard_id": 0,
    "num_shards": 1,
    "selection_policy": "manifest_index_mod_num_shards",
    "input_shard_manifest_sha256": "<sha256>"
  },
  "runtime": {
    "device": "<device>",
    "precision": "float32",
    "batch_size": 0,
    "determinism_policy": "<explicit>",
    "created_by": "<command/module>",
    "created_at": "<UTC timestamp>",
    "certgen_version": "<version>"
  },
  "source": {
    "license_status": "<explicit>",
    "provenance_ledger_sha256": "<sha256>"
  },
  "evidence": {
    "status": "real_features_unvalidated",
    "claim_allowed": false
  }
}
```

Zero values above are schema placeholders, not valid cache values.

## Validation rules

### Structural

- Every displayed object and field is required; nullable hashes must be accompanied by an explicit reason when unavailable.
- `shape` must contain two positive integers and equal `[number of sample IDs, feature_dim]`.
- Dtype must be an allowed finite floating type.
- All paths must be relative to an explicitly supplied artifact root; absolute user paths are rejected from portable outputs.
- Unknown schema versions are blocked, not guessed.

### Array and identity integrity

- The NPZ must contain both `features` and `sample_ids`.
- Every feature value must be finite; empty and constant caches are rejected for real-pilot use.
- Sample IDs must be non-empty, unique, and in exact row order.
- The sidecar's ordered-sample-ID hash and NPZ hash must match.
- Source-manifest IDs for the declared role must match the NPZ IDs exactly; missing, extra, reordered, duplicated, or cross-role IDs are errors.
- Image hashes, when available, must be checked for duplicate images, reference/generated overlap, and shard overlap before feature promotion.

### Extractor and preprocessing compatibility

- Caches compared by one metric must have the same extractor name, immutable model/revision, output layer, feature dimension, package-major convention, preprocessing lock, dtype policy, and feature-normalization policy unless the metric specification explicitly allows otherwise.
- Inception, CLIP, and DINOv2 require separate preprocessing locks.
- Caller-requested IDs are not sufficient; the resolved model/weights/processor must be recorded.
- FID requests require a declared compatible Inception convention. A generic `custom` escape hatch cannot make an unknown extractor compatible with FID.

### Shards and merge

- A merge requires exactly one valid shard for every ID in `[0, num_shards)`.
- All shard invariant fields must match.
- Each shard's row set must equal its deterministic manifest selection, and shard row sets must be disjoint.
- Merge order is canonical sample-ID order. The merged sidecar records every source sidecar/hash rather than copying only the first sidecar as a template.

### Evidence state

- New extraction starts as `real_features_unvalidated` with `claim_allowed=false`.
- Structural validation does not promote a cache to paper evidence.
- Strict content hashes, provenance, source/license, compatibility, and metric reproduction are separate required gates.
- Warnings that affect extractor identity, preprocessing, sample identity, hashes, or license are blocking for a real pilot.

## Migration and backward compatibility

The local migrator now provides this behavior:

```text
read legacy sidecar -> classify dialect -> validate available fields ->
write <original>.certgen-v2.json -> revalidate -> emit migration report
```

The command must:

- never overwrite the legacy sidecar or NPZ;
- copy only verifiable values;
- use `null` plus a blocker reason for unavailable identity fields;
- recompute the NPZ and ordered-ID hashes;
- preserve the original evidence status but force `claim_allowed=false`;
- refuse migration when sample IDs are absent, duplicated, or cannot be bound to the source manifest;
- record old and new sidecar hashes and the converter version.

Legacy readers may continue for smoke fixtures. Real-like certificate gates now require `schema_version=certgen.feature_cache.v2` in an adjacent sidecar after the reference draw-plan gate passes.

Canonical commands:

```bash
python3 -m certgen.features.cache_v2 migrate --features <cache.npz> --legacy-sidecar <cache.json> --out-sidecar <cache.certgen-v2.json> --artifact-root <run-root> --role <role> --dataset-id <dataset> --split <split> --source-manifest <relative-manifest.jsonl> --model-id <model> --checkpoint <revision>
python3 -m certgen.features.cache_v2 validate --features <cache.npz> --sidecar <cache.json> --artifact-root <cache-root>
```

Migration deliberately writes unresolved values and returns a blocked result instead of guessing. The certificate gate prefers a non-destructive adjacent `<stem>.certgen-v2.json` sidecar and falls back to `<stem>.json` only when that file already uses the v2 schema.

## Import transaction

Copied-back archives must be handled as a transaction:

1. hash and preserve the raw ZIP;
2. path-safely extract to a fresh temporary/versioned directory;
3. validate archive structure and every cache contract;
4. compare against any existing destination;
5. if identical, report idempotent reuse;
6. if different, preserve both and require an explicit selection record;
7. atomically update a pointer/manifest only after success.

No validator may call `rmtree` on the active cache before the incoming cache passes.

## Required error codes

At minimum: `SCHEMA_VERSION_UNSUPPORTED`, `ARRAY_HASH_MISMATCH`, `SIDECAR_HASH_MISMATCH`, `SAMPLE_IDS_MISSING`, `SAMPLE_IDS_DUPLICATED`, `SAMPLE_IDS_REORDERED`, `SOURCE_MANIFEST_MISMATCH`, `ROLE_MISMATCH`, `EXTRACTOR_MISMATCH`, `PREPROCESSING_MISMATCH`, `FEATURE_DIM_MISMATCH`, `NONFINITE_FEATURES`, `EMPTY_CACHE`, `SHARD_SET_INCOMPLETE`, `SHARD_OVERLAP`, `LICENSE_BLOCKED`, and `DESTINATION_CONFLICT`.

## Current blocker

The validator, non-destructive migrator, and real-like certificate gate are implemented and covered by fixture tests. No real cache has been migrated or validated. Existing V3 cache validation remains useful for smoke and preliminary integrity checks but cannot authorize a real metric-reproduction or certificate pilot.
