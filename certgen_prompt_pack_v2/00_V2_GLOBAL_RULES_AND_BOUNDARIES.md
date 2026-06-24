# Prompt 00 — V2 Global Rules and Boundaries

## Task

Read this first before making any CertGen V2 changes. Apply these rules to every later V2 prompt.

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

## Current V1 baseline

Assume the repo already has:

- `certgen/` package.
- Config validation.
- Smoke artifact generation.
- Registry validation.
- First-pilot plan generation.
- V1 final audit.
- Claim gates.
- Conservative FID/FD-DINOv2 descriptive-only policy.
- 33 passing tests.

Do not remove any V1 guard unless a V2 prompt explicitly replaces it with a stricter guard.

## V2 scope

V2 may add:

- Clean metric contribution streams.
- MMD/KID/CMMD certificate code.
- Anytime-valid confidence sequence/e-process modules.
- Optional-stopping validity lab.
- Feature-cache contracts.
- First-pilot dry-run path.
- Registry availability fields.
- V2 audit and handoff docs.

V2 may not add:

- Real benchmark claims.
- Real undecided fraction claims.
- Real ranking movement claims.
- Paper-ready tables with real numbers unless a real audit is actually executed later.
- Mandatory GPU extraction in tests.
- FID rigorous certification without a proof-backed implementation.

## Done criteria

After every prompt run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

must pass, or the failure must be documented as an intentional blocker with a fix plan.
