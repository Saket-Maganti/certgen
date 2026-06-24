# Prompt 12 — V2 Final Audit and Handoff

## Role

You are writing the V2 audit that decides whether CertGen is ready for the V3 first real pilot. The audit must be strict and conservative.

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

Implement a V2 final audit command and produce a single-file V2 handoff.

## Required files

Create or update:

```text
certgen/audit/v2_audit.py
certgen/cli/v2_audit.py
tests/test_v2_audit.py
docs/V2_FINAL_AUDIT.md
docs/V2_SINGLE_FILE_HANDOFF.md
data/results/v2_final_audit.json
```

## Required audit checks

At minimum, check:

1. V1 tests still pass or V2 test suite passes.
2. Clean-core MMD/KID/CMMD stream code exists.
3. CS implementation exists with documented assumptions.
4. Certificate API exists.
5. Optional-stopping lab exists and is smoke-labeled.
6. Feature-cache schema exists.
7. Registry V2 availability fields exist.
8. First-pilot V2 dry-run planner exists.
9. FID/FD-DINOv2 rigorous claims are blocked.
10. Smoke/demo artifacts cannot become evidence.
11. Certificate reports include not-evidence warnings for smoke outputs.
12. No forbidden claim phrases appear in docs/results.
13. Heavy dependencies are optional/lazy.
14. No GPU command runs in tests.
15. Final handoff states no real empirical evidence yet.

## CLI example

```bash
python3 -m certgen.cli.v2_audit   --out docs/V2_FINAL_AUDIT.md   --json-out data/results/v2_final_audit.json
```

## Single-file handoff content

`docs/V2_SINGLE_FILE_HANDOFF.md` must include:

- V1 starting point.
- V2 implemented changes.
- Test command and result placeholder.
- Commands added.
- What is still non-evidence.
- FID policy.
- Exact next V3 action.
- Go/no-go number for V3: first-benchmark undecided fraction.

## Done criteria

- V2 audit passes only if all required guards exist.
- Audit JSON is machine-readable.
- Handoff is honest and complete.
