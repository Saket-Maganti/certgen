# Prompt 06 — CMMD/KID/MMD Integration Tests and Fixtures

## Role

You are adding integration tests that prove the V2 clean-core system works end-to-end on tiny synthetic feature fixtures, without making empirical claims.

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

Create deterministic synthetic feature fixtures and integration tests for KID/MMD/CMMD-style certificate flows.

## Required files

Create or update:

```text
certgen/fixtures/make_v2_feature_fixtures.py
tests/test_v2_clean_metric_integration.py
docs/V2_FIXTURE_POLICY.md
```

Optional CLI:

```bash
python3 -m certgen.fixtures.make_v2_feature_fixtures   --out-dir data/smoke/v2/features   --seed 0
```

## Required fixtures

Generate small NumPy feature arrays:

1. `reference.npz`
2. `model_a_close.npz`
3. `model_b_far.npz`
4. `model_a_far.npz`
5. `model_b_close.npz`
6. `model_equal_1.npz`
7. `model_equal_2.npz`

Each fixture must include:

- features array;
- metadata JSON sidecar;
- evidence status `smoke_only`;
- seed;
- generation parameters;
- warning that fixtures are synthetic and non-evidence.

## Required integration cases

Test:

- A certified better on easy synthetic case.
- B certified better on reversed case.
- Not decided on equal/near-equal case.
- CMMD label works using same feature machinery.
- KID polynomial works.
- RBF MMD works.
- claim gate blocks evidence promotion.

## Documentation

`docs/V2_FIXTURE_POLICY.md` must say:

- fixtures are only for software validation;
- fixtures cannot support paper claims;
- passing integration tests does not imply CertGen has empirical results.

## Done criteria

- Integration tests pass.
- Fixture generation is deterministic.
- Smoke labels are visible in every generated file.
