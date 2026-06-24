# Prompt 08 — Dry-Run-Safe First-Pilot Path

## Role

You are creating the first path toward real CertGen evidence, but this prompt must remain dry-run-safe. The output should plan and validate a first pilot, not execute heavy feature extraction or make claims.

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

Upgrade the V1 first-pilot planner into a V2 dry-run-safe first-pilot pipeline that checks whether one benchmark/model-pair plan is ready for feature extraction and certification later.

## Required files

Create or update:

```text
certgen/pilot/first_pilot_v2.py
certgen/cli/plan_first_pilot_v2.py
tests/test_first_pilot_v2.py
docs/V2_FIRST_PILOT_DRY_RUN.md
```

## Required planner inputs

The planner should read registry files for:

- candidate benchmarks;
- candidate model pairs;
- released sample availability;
- feature cache status;
- claimed/reported metrics to audit;
- preprocessing assumptions;
- license/source notes.

## Required outputs

```text
data/results/v2_first_pilot_plan.json
docs/V2_FIRST_PILOT_PLAN.md
```

The plan must include:

- selected benchmark or `none_selected`;
- selected model pairs or reasons unavailable;
- required features;
- missing artifacts;
- expected clean-core metrics;
- FID descriptive policy;
- exact next commands;
- evidence status `dry_run_only`;
- claim status `NO_REAL_CLAIMS_ALLOWED`.

## CLI example

```bash
python3 -m certgen.cli.plan_first_pilot_v2   --registry-dir registry   --out-json data/results/v2_first_pilot_plan.json   --out-md docs/V2_FIRST_PILOT_PLAN.md   --dry-run
```

## Selection policy

Do not auto-select a pilot if required fields are missing. Prefer `needs_user_verification` over guessing.

The first pilot should prefer:

1. public/free benchmark;
2. released generated samples or verified checkpoint/sample source;
3. manageable sample count;
4. known reported metric gap;
5. explicit preprocessing info;
6. clean license/source status.

## Tests

Add tests for:

- complete smoke registry selects a pilot;
- missing released samples blocks pilot;
- unknown license blocks real-ready status;
- missing preprocessing blocks certificate-ready status;
- plan labels dry-run only;
- no claims are allowed.

## Done criteria

- V2 planner can produce a dry-run plan.
- The plan is useful but conservative.
- It never invents availability.
