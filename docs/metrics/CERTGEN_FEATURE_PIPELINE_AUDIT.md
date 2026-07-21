# CertGen Feature Pipeline Audit

Status: `VERIFIED_CURRENT_CODE_AUDIT`

Evidence boundary: `synthetic_validation_only`, `not_model_evidence`, `claim_allowed=false`.

This document describes the repository as inspected on 2026-07-11. It does not report a real feature run. No validated real CIFAR-10 Inception or CLIP cache is present under `data/features`, and the live R1D/R1E artifacts remain blocked on feature extraction.

## Executive verdict

The repository has a guarded extraction path, deterministic shard assignment, role splitting, hash fields, and CPU-side validators. It is sufficient to plan a run, but it is not yet safe to promote copied-back caches to a metric-reproduction or certificate gate. The current sidecar formats are inconsistent, extractor identity is not recorded reliably, shard compatibility is under-validated, and import is not yet a temporary/versioned validation transaction.

## Live pipeline

1. `certgen.packaging.build_kaggle_feature_input_zip` packages manifests, one preprocessing lock, and the requested extractor list.
2. The Kaggle notebook invokes `certgen.features.extract` for two shards per extractor.
3. `certgen.features.extractors.base.FeatureExtractor.extract` writes an NPZ and JSON sidecar.
4. `certgen.features.merge_shards` sorts rows by sample ID and writes one merged cache.
5. `certgen.features.split_by_role` joins sample IDs to the sample manifest and writes role caches.
6. `certgen.features.cache_validate.validate_v3_feature_cache` checks shape, dtype, finiteness, selected preprocessing fields, license status, and an optional hash.
7. `certgen.pipeline.v6_execution.run_r1d_metric_reproduction_gate` consumes the role-cache checks.

## Implemented capabilities

| Capability | Current state | Evidence |
|---|---|---|
| Heavy model loading requires explicit execution | Implemented | `certgen/cli/run_feature_extraction.py` defaults to a dry-run plan; real extraction requires `--execute`. |
| Lazy optional dependencies | Implemented | Torch, torchvision, transformers, and PIL are imported inside extractor hooks. |
| Shard assignment | Deterministic | Manifest row `i` goes to shard `i % num_shards`. |
| Merge ordering | Deterministic but incomplete | Rows are sorted lexically by sample ID, but shard compatibility and completeness are not established first. |
| Shape and finite-value checks | Implemented | The V3 validator checks a 2D floating array, declared row count/dimension, and finite values. |
| Cache content hash | Partially implemented | Hashes are written, but strict checking is optional in several real-pilot paths. |
| Sample identity checks | Insufficient | Missing arrays produce warnings; duplicate IDs, sidecar/NPZ ID disagreement, and reordered IDs are not rejected. |
| Extractor/preprocessing identity | Insufficient | Exact resolved weights, package versions, processor revision, and per-extractor lock are not reliably recorded. |
| Atomic/versioned import | Missing | Current hardening refuses an existing destination, but extracts into the final destination before cache-content validation succeeds. |

## Extractor audit

### Inception V3 pool3

- The adapter always loads torchvision `Inception_V3_Weights.IMAGENET1K_V1` and replaces the final fully connected layer with an identity map.
- The declared output dimension is 2048.
- The public `model_id` argument is ignored by the loader but copied verbatim into the sidecar. A caller can therefore create a sidecar that names weights that were not loaded.
- The implementation is not the canonical TensorFlow-ported FID Inception pipeline. FID/KID reproduction against a published target must remain blocked unless the target used this exact torchvision convention or a canonical adapter is implemented.

### CLIP ViT

- The default loader is `openai/clip-vit-large-patch14`; the declared default output dimension is 768 and is replaced by the loaded projection dimension at runtime.
- When the default is used, the base sidecar records the caller value `model_id=null`, not the resolved default model identifier.
- The CLIP processor controls resizing and normalization, but the sidecar records the externally supplied preprocessing dictionary. The current feature package contains only the Inception preprocessing lock, and both current Kaggle feature notebooks pass that same lock to Inception and CLIP. The recorded CLIP preprocessing can therefore be false.

### DINOv2

- The default loader is `facebook/dinov2-base`, with its loaded hidden size used as the feature dimension.
- FD-DINOv2 is correctly routed to descriptive-only use, but the same resolved-model and package-version recording gaps apply.

## Unresolved defects

### P0 — must be repaired before accepting a copied-back cache

1. **Import is not transactional.** The inspected baseline of `certgen/packaging/validate_kaggle_feature_output_zip.py` removed `extract_dir` before validation. Concurrent hardening now refuses to overwrite an existing directory, which closes the data-loss path, but it still extracts into the final destination before cache-content checks run. A failed content check can leave an invalid active-looking directory that blocks retry. Extraction must occur in a temporary/versioned directory; promotion must be atomic and only after all checks pass.
2. **Structure-only importer can report readiness without validating cache contents.** `certgen/packaging/import_kaggle_feature_outputs.py` checks ZIP safety, required filenames, a status JSON, roles, and families, but it does not load the NPZ arrays or run the cache validator. Recent hardening correctly blocks the older empty-JSON fixture, leaving its legacy test stale, but the command remains an inventory check rather than a complete importer or cache-validation transaction.
3. **False preprocessing provenance for CLIP.** A single Inception lock is packaged and passed to both extractors, while the CLIP adapter ignores it and the base writer records it. Separate extractor locks and resolved processor metadata are required.
4. **Sample identity is not enforced.** The V3 validator does not compare NPZ sample IDs with sidecar IDs or reject duplicates. A local diagnostic cache with duplicate IDs passed strict hash validation. Cross-role image/sample overlap is also not checked at the feature gate.

### P1 — required before the first technical pilot

1. `merge_feature_shards` does not require a complete shard index set and does not compare extractor, resolved model, preprocessing, source-manifest hash, preprocessing-lock hash, feature dtype, or declared shard count across shards.
2. `--resume` in `certgen.features.extract` does not resume or skip a validated shard. Existing output is allowed when `resume=True`, then extraction runs again and overwrites it. The Kaggle notebooks advertise this as resume support.
3. `split_feature_cache_by_role` silently overwrites duplicate sample IDs in its manifest lookup and does not bind the output to the actual sample-manifest hash it consumed.
4. Real-pilot call sites use `strict_hash=False` in several paths. A real cache must never be considered validated without a content hash match.
5. Vision dependencies are unpinned in `pyproject.toml`; model revisions, checkpoint hashes, processor revisions, precision, package versions, and deterministic-backend settings are missing from sidecars.
6. Feature writes and JSON writes are not atomic. An interrupted write can leave a partial NPZ or a data/sidecar mismatch.

### P2 — maintainability and release hardening

1. Three incompatible feature metadata dialects coexist: `FeatureCacheManifest`, `FeatureManifest`, and the loose V3/extractor sidecar.
2. Sidecar suffixes vary between `.json`, `.sidecar.json`, and metadata JSON.
3. Old smoke-only metric and pilot paths are not clearly deprecated from the live V6 path.

## Required local-safe tests

- Reject duplicate, missing, reordered, or sidecar-mismatched sample IDs.
- Reject empty caches, partial shard sets, duplicated shard IDs, and mixed shard metadata.
- Reject extractor, model revision, preprocessing lock, role, dtype, and feature-dimension mismatches.
- Verify that a failed import preserves a sentinel in the existing destination and leaves the incoming ZIP untouched.
- Verify idempotent resume: a hash-valid completed shard is skipped; an invalid shard is refused unless an explicit replacement policy is selected.
- Verify deterministic merge bytes or, where NPZ container metadata prevents byte identity, deterministic row order and canonical content hashes.
- Verify each extractor records its resolved model/weights/processor and its own preprocessing lock.

## Stop condition

Feature extraction may proceed only after the input sample package passes its existing gates. Certificate execution must remain blocked until the imported caches satisfy the canonical cache contract, the metric specification is frozen, and the reproduction protocol in `CERTGEN_METRIC_REPRODUCTION_PROTOCOL.md` passes. Passing unit tests or creating notebooks does not satisfy that condition.
