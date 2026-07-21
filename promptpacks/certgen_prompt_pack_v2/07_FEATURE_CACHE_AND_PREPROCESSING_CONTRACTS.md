# Prompt 07 — Feature Cache and Preprocessing Contracts

## Role

You are preparing CertGen for real first-pilot feature extraction without actually requiring heavy extraction in tests.

## Global rules that apply to this prompt

- Preserve V1 behavior and backward compatibility unless the prompt explicitly asks for a breaking change.
- Do not fabricate real results, benchmark numbers, model rankings, citations, sample availability, or claim language.
- Do not promote smoke, mock, synthetic, fixture, planned, or dry-run outputs into evidence.
- Keep tests CPU-only and small. No GPU job may run inside normal tests.
- Keep heavy imports lazy and optional. The repo must remain usable without torch/torchvision/transformers unless a command explicitly requests feature extraction.
- FID and FD-DINOv2 remain descriptive unless a mathematically valid FID/FD certificate is explicitly implemented and audited. Do not weaken this policy.
- No paid APIs, no paid cloud, no paid datasets, no paid annotation, no hosted inference.
- Mark every generated artifact with evidence status: `smoke_only`, `dry_run_only`, `planned`, `descriptive_only`, or `eligible_after_real_run` as appropriate.
- Every new command must have docs, help text, tests, and an example invocation.
- Every claim-producing path must pass through claim gates.
- If a real run is not executed, output files must explicitly say `NO_REAL_EVIDENCE` or equivalent.
- Do not initialize git, commit, tag, or push.

## Task

Define the feature cache schema, preprocessing contract, and provenance requirements for future real image/video features.

## Required files

Create or update:

```text
certgen/features/cache_schema.py
certgen/features/validate_cache.py
certgen/features/preprocessing.py
certgen/cli/validate_feature_cache.py
tests/test_feature_cache_schema.py
docs/V2_FEATURE_CACHE_CONTRACT.md
```

## Feature cache manifest schema

A feature cache manifest should include:

- `cache_id`
- `dataset_id`
- `split`
- `sample_source_type`: `released_samples`, `local_images`, `precomputed_features`, `smoke_fixture`
- `model_or_generator_id`
- `feature_extractor`: `inception`, `clip`, `dinov2`, `i3d`, etc.
- `feature_extractor_version`
- `preprocessing_policy_id`
- `resize_size`
- `crop_policy`
- `interpolation`
- `normalization`
- `num_samples`
- `feature_dim`
- `feature_file_path`
- `feature_file_sha256`
- `source_license_status`
- `download_or_local_source_note`
- `evidence_status`
- `created_at`

## Preprocessing contract

Create a strict object or YAML schema for preprocessing policies.

Rules:

- Do not allow vague preprocessing such as `default` without details.
- Interpolation must be explicit.
- Resize/crop must be explicit.
- Feature extractor must be explicit.
- Recomputed published scores must record matched preprocessing assumptions.

## Validator

Implement CLI:

```bash
python3 -m certgen.cli.validate_feature_cache   --manifest registry/feature_caches/smoke_feature_cache_manifest.json
```

Validator must fail if:

- feature file missing;
- hash mismatch;
- shape mismatch;
- preprocessing fields missing;
- license/source status unknown;
- evidence status invalid;
- real-evidence status requested without source/provenance gates.

## Tests

Add tests for valid smoke cache and several invalid cache manifests.

## Documentation

`docs/V2_FEATURE_CACHE_CONTRACT.md` must explain why preprocessing matters for FID/KID/CMMD reproducibility.

## Done criteria

- Cache validator works on smoke fixture caches.
- Real feature extraction remains optional and not required for tests.
