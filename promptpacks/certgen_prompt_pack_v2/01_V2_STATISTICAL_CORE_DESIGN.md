# Prompt 01 — V2 Statistical Core Design

## Role

You are upgrading CertGen from a V1 smoke scaffold into a V2 clean-core statistical engine. Your job is to design the internal statistical contracts before writing heavy implementation.

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

## Inputs to assume

- V1 has a smoke certificate scaffold using a labeled Hoeffding-style bound.
- V1 has no final statistical implementation.
- FID and FD-DINOv2 are descriptive-only.

## Task

Create a V2 statistical design document and lightweight module skeletons for clean metric comparison.

## Required design document

Create:

```text
docs/V2_STATISTICAL_CORE_DESIGN.md
```

It must cover:

1. The comparison target:

```text
Delta_AB = d(A, R) - d(B, R)
```

where lower is better.

2. Metric classes:

- Clean-core certifiable metrics: MMD/KID/CMMD-style metrics with contribution streams.
- Descriptive metrics: FID and FD-DINOv2 unless later made rigorous.

3. Data model:

- Feature arrays for model A, model B, and reference real samples.
- Required shapes and dtype handling.
- Deterministic seeded batching and pairing.
- Optional streaming mode.

4. Contribution-stream design:

- `h_i` per comparison unit.
- Direction convention: negative means A better, positive means B better.
- Bounded or clipped contributions for conservative CS.
- Metadata about clipping/truncation.

5. Confidence-sequence target:

- A time-uniform interval for `E[h_i]`.
- Stop when interval excludes 0.
- Otherwise output `not_decided_at_budget`.

6. Risks and limitations:

- Dependence between terms.
- Feature reuse and paired reference samples.
- Kernel choice sensitivity.
- Boundedness/clipping tradeoff.
- FID nonlinearity.

7. V2 claim policy:

- A V2 certificate may certify only smoke/demo streams unless real feature provenance and registry gates pass.

## Required module skeletons

Create or update:

```text
certgen/stats/__init__.py
certgen/stats/design_contracts.py
certgen/stats/streams.py
certgen/stats/cs.py
```

Skeletons should include typed dataclasses/interfaces, not full heavy implementation yet unless useful.

Minimum dataclasses:

- `FeatureSet`
- `ComparisonStream`
- `CSConfig`
- `CSResult`
- `DecisionCertificate`

## Tests

Add tests that verify:

- Direction convention is documented and enforced.
- FID/FD-DINOv2 cannot be marked `rigorous_certified` by default.
- Smoke/demo evidence status remains non-evidence.

## Commands

No new CLI required in this prompt unless existing architecture expects it.

## Done criteria

- `docs/V2_STATISTICAL_CORE_DESIGN.md` exists.
- New modules import without heavy dependencies.
- Tests pass.
