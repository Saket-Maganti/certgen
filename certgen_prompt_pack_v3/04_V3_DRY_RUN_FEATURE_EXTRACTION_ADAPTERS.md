# Prompt 04 — Dry-Run Feature Extraction Adapters

Implement dry-run-safe feature extraction adapters without requiring heavy model downloads in tests.

## Goal

Provide commands and interfaces for future real feature extraction, but keep V3 tests offline and lightweight.

Create/upgrade:

- `certgen/features/extractors/base.py`
- `certgen/features/extractors/inception.py`
- `certgen/features/extractors/clip.py`
- `certgen/features/extractors/dinov2.py`
- `certgen/cli/plan_feature_extraction.py`
- `docs/FEATURE_EXTRACTION_RUNBOOK_V3.md`

## Adapter interface

Each extractor should expose:

```python
class FeatureExtractor:
    name: str
    feature_dim: int
    heavy_dependencies: list[str]

    def is_available(self) -> bool: ...
    def dry_run_plan(self, input_manifest, out_dir, batch_size, device) -> dict: ...
    def extract(self, input_manifest, out_dir, batch_size, device, max_items=None) -> dict: ...
```

For V3:
- `dry_run_plan` must work without torch/torchvision/transformers installed.
- `extract` can raise a clear `OptionalDependencyMissing` error if dependencies are absent.
- No actual model download should occur unless user explicitly runs extraction command with dependencies available.

## Input manifest

Support JSONL rows:

```json
{
  "sample_id": "...",
  "path": "...",
  "source_type": "reference_real|generated_sample",
  "model_id": "...",
  "benchmark_id": "..."
}
```

## Planning CLI

```bash
python3 -m certgen.cli.plan_feature_extraction \
  --input-manifest registry/manifests/first_pilot_samples_template.jsonl \
  --extractor inception_v3_pool3 \
  --out-dir data/features/first_pilot/inception \
  --device auto \
  --batch-size 32 \
  --dry-run \
  --out docs/FEATURE_EXTRACTION_PLAN.md \
  --json-out data/results/feature_extraction_plan.json
```

## Plan output should include

- item count;
- missing local files count;
- estimated batches;
- device request;
- extractor availability;
- whether heavy dependencies are needed;
- output paths that would be created;
- evidence status `dry_run_only`;
- claim_allowed false.

## Tests

- Use fake local image manifest paths in temp dirs.
- Test dry-run plan without heavy dependencies.
- Test missing path warnings.
- Test invalid extractor name.
- Test extraction raises optional dependency error when unavailable.

## Docs

Runbook should cover:
- Kaggle feature extraction later;
- how to cache `.npz` + sidecar;
- exact preprocessing requirements;
- no claims from extraction alone.

## Verification

Run pytest and the dry-run planning CLI.
