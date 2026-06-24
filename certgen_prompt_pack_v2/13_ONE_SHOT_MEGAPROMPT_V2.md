# CertGen V2 One-Shot Megaprompt

Use this only if you want to attempt the full V2 upgrade in one run. Prefer the staged prompts for safer execution.

## Mission

Upgrade the existing CertGen V1 repo into V2.

V1 baseline:
- V1 audit passed 15/15.
- Tests passed: 33 passed, 0 failed.
- V1 has repo scaffold, configs, docs, registry, smoke outputs, claim gates, and conservative FID/FD descriptive-only policy.
- V1 clean certificate is only a smoke scaffold, not final V2 statistics.

V2 goal:
Build the clean-core KID/MMD/CMMD certificate engine, optional-stopping validity lab, feature-cache contracts, first-pilot dry-run path, registry upgrades, reporting cards, and final V2 audit.

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

## Implement all of the following

### A. Statistical core design

Create `docs/V2_STATISTICAL_CORE_DESIGN.md` and module contracts under `certgen/stats/`.

### B. MMD/KID/CMMD streams

Implement NumPy-only kernels, MMD estimates, linear-time stream contributions, and clipping metadata under `certgen/metrics/`.

### C. Confidence sequences

Implement conservative time-uniform Hoeffding-style CS and empirical-Bernstein/e-process-style CS for bounded streams. Label assumptions and theory status honestly.

### D. Certificate API

Create a high-level API/CLI for clean metric comparison certificates over `.npz`/`.npy` feature arrays.

### E. Optional-stopping lab

Create CPU-only synthetic simulations comparing naive peeking versus CertGen CS. Outputs must be smoke-only and not paper evidence.

### F. Feature-cache contract

Create schema and validator for feature cache manifests, including preprocessing details and hashes.

### G. Registry V2

Add released-sample availability, reported metric claims, audit eligibility, and blocking reasons.

### H. First-pilot dry-run planner

Plan one verified benchmark/model-pair route without running heavy extraction or making claims.

### I. FID policy

Reinforce FID/FD-DINOv2 descriptive-only policy. Block rigorous FID claims by default.

### J. Reporting

Render certificate cards and V2 summaries with visible not-evidence warnings.

### K. V2 final audit

Implement `v2_audit`, write `docs/V2_FINAL_AUDIT.md`, `data/results/v2_final_audit.json`, and `docs/V2_SINGLE_FILE_HANDOFF.md`.

## Required final commands

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Then run the V2 audit command, using the repo's CLI conventions.

## Output summary required at end

Report:

- files changed;
- tests passed/failed;
- audit passed/failed;
- commands added;
- limitations;
- exact next V3 prompt/action.

## Non-negotiable final state

There must still be no real empirical claim, no undecided fraction claim, no ranking movement claim, and no rigorous FID certificate claim.
