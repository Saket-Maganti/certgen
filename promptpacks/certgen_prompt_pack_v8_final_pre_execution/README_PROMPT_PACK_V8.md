# CertGen Prompt Pack V8 — Final Pre-Execution Hardening + Run Unblocker

This prompt pack is the final upgrade before real execution. It exists because V7 made the repo execution-capable but still ended at `BLOCKED_MISSING_REFERENCE_SAMPLES`.

## What V8 must accomplish

1. Make CIFAR-10 reference materialization foolproof from a local image tree, official archive, torchvision cache, or explicit user-approved download.
2. Make Kaggle T4x2 generation and feature-extraction bookruns stronger, resumable, and ZIP/copy-back safe.
3. Add execution ledger, run dashboard, and blocker triage only where they directly help real runs.
4. Add local import/validation repair for common Kaggle output failures.
5. Add exact runtime estimate tables and measured-runtime log slots.
6. Enforce a hard post-V8 stop: no V9, no more generic scaffolding, only real CIFAR execution.

## Staged execution order

Run the numbered prompts in order:

00 through 15, then 17. Read 16 only if you want a one-shot controller.

## Expected final V8 state

- Tests pass.
- V8 final audit passes.
- Final execution audit is either:
  - `READY_FOR_KAGGLE_GENERATION`, if CIFAR reference was found/materialized; or
  - `BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE`, with exact paths and commands.
- Kaggle `.ipynb` bookruns are validated and resumable.
- Input/output ZIP flows are validated with fake fixtures.
- No fake empirical results.
- No `claim_allowed=true`.
- No paper evidence promotion.
- No certificates unless real feature caches and sanity gates pass.

## Non-negotiable stop rule

After V8, do not build more prompt packs. Start execution:

1. Materialize CIFAR reference.
2. Run Kaggle 1k/model generation.
3. Import generation ZIP.
4. Build feature package.
5. Run Kaggle feature extraction.
6. Import feature ZIP.
7. Run CPU sanity gates.
8. Run first certificate pilot.
