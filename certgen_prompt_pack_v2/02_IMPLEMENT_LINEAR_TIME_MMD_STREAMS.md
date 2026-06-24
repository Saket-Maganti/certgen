# Prompt 02 — Implement Linear-Time MMD/KID/CMMD Contribution Streams

## Role

You are implementing the clean-core metric contribution streams for CertGen V2. This is the foundation for KID/MMD/CMMD certificates.

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

Implement CPU-only feature-array metric streams for MMD/KID/CMMD-style comparisons.

## Required files

Create or update:

```text
certgen/metrics/kernels.py
certgen/metrics/mmd.py
certgen/metrics/streams.py
certgen/metrics/__init__.py
tests/test_mmd_streams.py
```

## Required functionality

### 1. Kernels

Implement pure NumPy kernels:

- `linear_kernel(x, y)`
- `polynomial_kernel(x, y, degree=3, gamma=None, coef0=1.0)`
- `rbf_kernel(x, y, gamma=None)`

Rules:

- No torch required.
- Validate shapes.
- Support 2D arrays only: `[n, d]`.
- Use stable float64 internally.
- Return NumPy arrays.

### 2. MMD estimates

Implement:

- unbiased quadratic MMD estimate for fixed-n diagnostics;
- linear-time paired MMD contribution stream for sequential use.

The stream function should accept feature arrays for generated model samples and reference samples and return per-unit contributions.

For pairwise comparison A vs B against the same reference R, implement:

```python
mmd_difference_stream(features_a, features_b, features_r, kernel_config, seed=0, max_units=None)
```

It must return a `ComparisonStream` where each unit estimates contribution to:

```text
MMD^2(A, R) - MMD^2(B, R)
```

Direction:

- negative stream mean => A closer to R / A better;
- positive stream mean => B closer to R / B better.

### 3. CMMD support

CMMD is not a separate math object in V2. It is MMD applied to CLIP-like features. Implement metric labels/configs so a stream can be tagged as:

- `kid_polynomial`
- `mmd_rbf`
- `cmmd_clip_mmd`

Do not require CLIP extraction in tests.

### 4. Bounded/clipped streams

Add a utility:

```python
clip_stream_values(values, lower, upper)
```

It must record clipping metadata:

- lower bound
- upper bound
- number clipped low
- number clipped high
- fraction clipped

Do not silently clip without metadata.

## Tests

Add tests for:

- zero MMD when arrays are identical within tolerance;
- positive MMD for clearly separated synthetic distributions;
- direction convention using A closer than B and B closer than A;
- deterministic stream with seed;
- shape validation;
- no heavy dependency import;
- clipping metadata correctness.

## Documentation

Update or create:

```text
docs/V2_MMD_STREAMS.md
```

Explain:

- why linear-time streams are used for sequential certificates;
- difference between diagnostic quadratic MMD and sequential stream contributions;
- direction convention;
- CMMD-as-feature-space-MMD framing.

## Done criteria

- MMD stream tests pass.
- Existing V1 tests pass.
- No real claims are produced.
