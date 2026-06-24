# Prompt 03 — Empirical-Bernstein / E-Process Confidence Sequences

## Role

You are implementing the V2 confidence-sequence core for bounded clean metric contribution streams. Be conservative and honest. If a formula is implemented as a conservative practical bound rather than a state-of-the-art proof, label it clearly.

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

Replace the V1 labeled smoke certificate scaffold with a tested V2 confidence-sequence module for bounded streams.

## Required files

Create or update:

```text
certgen/stats/bounds.py
certgen/stats/cs.py
certgen/certs/clean_core.py
tests/test_confidence_sequences.py
tests/test_clean_core_certificate.py
```

## Required CS variants

Implement at least two variants:

### 1. Conservative time-uniform Hoeffding-style CS

Purpose: robust fallback for bounded streams.

Input:

- stream values `x_1, ..., x_t`
- lower/upper bounds `[a, b]`
- alpha
- time horizon/budget `T` if using a union-bound schedule

Must be valid under continuous monitoring by construction. A simple valid fallback is acceptable if it is explicitly conservative.

### 2. Empirical-Bernstein-style CS or e-process-style bound

Purpose: tighter practical V2 certificate.

Requirements:

- Use sample variance or betting/e-process logic.
- Must not be advertised as theoretically novel.
- Must include docstring references to assumptions.
- Must expose a `method_label` such as `empirical_bernstein_conservative` or `betting_cs_experimental`.
- If the implementation is not proof-complete, mark `theory_status='conservative_practical'` or `theory_status='experimental_not_for_paper_claims'`.

Do not pretend the experimental variant is the final proof if it is not.

## Certificate decision logic

For a stream estimating `Delta_AB`:

- If upper bound < 0: `A_certified_better`.
- If lower bound > 0: `B_certified_better`.
- If interval contains 0 at budget: `not_decided_at_budget`.
- If invalid input: `invalid_input`.

Certificate must include:

- `metric_label`
- `comparison_id`
- `alpha`
- `method_label`
- `time_uniform=True`
- `sample_units_seen`
- `budget_units`
- `mean_estimate`
- `lower`
- `upper`
- `decision`
- `evidence_status`
- `theory_status`
- `boundedness_metadata`
- `created_at`

## Tests

Add tests for:

- interval shrinks with more identical/similar bounded data;
- sign decision for synthetic negative-mean stream;
- sign decision for synthetic positive-mean stream;
- not decided when stream mean near zero;
- alpha validation;
- bound validation;
- optional monitoring metadata present;
- no decision produced for unbounded stream unless bounds/clipping are specified;
- evidence status remains `smoke_only` or `demo_only` for synthetic tests.

## Documentation

Create:

```text
docs/V2_CONFIDENCE_SEQUENCE_CORE.md
```

It must include:

- what is implemented;
- assumptions;
- what is conservative;
- what is experimental if anything;
- why this differs from fixed-n bootstrap/error bars;
- why FID is excluded from rigorous clean-core CS for now.

## Done criteria

- New CS tests pass.
- V1 tests still pass.
- No paper/result claims generated.
