# CertGen Canonical Interface

Status: `IMPLEMENTED_LOCAL`; all commands default to non-evidence outputs.

## Start here

```bash
python3 -m certgen status
python3 -m certgen next-action --write
```

The command prints one state transition. It does not claim a run succeeded because a notebook or package exists.

## Current reference gate

```bash
python3 -m certgen validate reference \
  --source /path/to/cifar-10-python.tar.gz \
  --explain
```

Accepted source classes are the official archive, extracted Python batches, or a complete image/class tree. The validator performs no automatic download. Materialization stays a separate state transition.

## Safe copied-back import

```bash
python3 -m certgen import preflight <zip>
python3 -m certgen import generation <zip>
python3 -m certgen import feature <zip>
```

Imports are allowlisted, resource-bounded, path-safe, atomic, run-specific, non-overwriting, hash-bound, and registered in `data/artifact_registry.jsonl`. A failed or partial status blocks import promotion.

## Feature cache contract

```bash
python3 -m certgen.features.cache_v2 migrate \
  --features <cache.npz> --legacy-sidecar <legacy.json> \
  --out-sidecar <cache.certgen-v2.json> --artifact-root <run-root> \
  --role <reference|model_a|model_b> --dataset-id <id> --split <split> \
  --source-manifest <relative.jsonl> --model-id <id> --checkpoint <revision>

python3 -m certgen.features.cache_v2 validate \
  --features <cache.npz> --sidecar <cache.certgen-v2.json> \
  --artifact-root <run-root>
```

Migration never overwrites the NPZ or legacy sidecar and never invents missing metadata. Unresolved fields return a blocked result.

## Reference sampling contract

```bash
python3 -m certgen.cli.build_reference_draw_plan \
  --manifest <validated-reference-manifest.jsonl> \
  --population-id cifar10_test_empirical \
  --num-draws <registered-draw-count> --seed <registered-seed> \
  --out <reference-draw-plan.json>
```

Build this only after the reference manifest is frozen and before viewing certificate values.

## Audits

```bash
python3 -m certgen audit notebooks
python3 -m certgen audit paper
python3 -m certgen audit artifact-registry
python3 -m certgen.audit.forensic_final_audit
```

## Verification lanes

```bash
# fast/default offline lane
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -m pytest -q

# statistical fast lane
python3 -m pytest -q tests/test_confidence_sequences.py tests/test_mmd_streams.py \
  tests/test_clean_core_certificate.py tests/test_reference_draw_plan.py

# artifact-contract lane
python3 -m pytest -q tests/test_engineering_evidence_safety.py \
  tests/test_feature_cache_v2_contract.py tests/test_v7_importers.py

# static quality
ruff check certgen tests
mypy certgen
```

Model/data/CUDA integration is opt-in and must never run as a side effect of default tests.

## Legacy policy

Existing `commands/v*_...` wrappers remain available to preserve historical workflows. They are deprecated as user-facing documentation whenever the canonical CLI covers the same transition. A wrapper must call package logic rather than copy safety/statistical logic.
