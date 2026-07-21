# V8 Prompt 12 — Notebook Idempotence and Dry-Run Validator


You are working on **CertGen** in `/Users/saketmaganti/Projects/certGen`.

Hard rule: this is **V8 Final Pre-Execution Hardening**, not V8 generic infrastructure.
Do not create V9. Do not add vanity scaffolding. Do not fabricate results. Do not promote anything to paper evidence.
All smoke/template/planning outputs must keep `claim_allowed=false`, `NO_FAKE_RESULTS`, and `not paper evidence`.

Current known state:
- V7 execution-development audit passed.
- Tests reached 169 passed after V7.
- Final execution audit remains `BLOCKED_MISSING_REFERENCE_SAMPLES`.
- Kaggle generation and feature-extraction bookruns exist.
- CPU/Kaggle ZIP handoff exists.
- No generation, feature extraction, metric sanity, certificate pilot, undecided fraction, or paper evidence exists.
- The immediate real blocker is missing CIFAR-10 reference samples.

V8 goal:
> Remove avoidable execution blockers, harden the CPU/Kaggle handoff, make CIFAR reference onboarding almost impossible to mess up, and end with a hard stop: after V8, only real execution.


## Objective

Prevent Kaggle notebooks from being one-shot fragile scripts.

## Build/upgrade

- `certgen/notebooks/validate_v8_kaggle_bookruns.py`
- `docs/V8_NOTEBOOK_IDEMPOTENCE_REPORT.md`
- `tests/test_v8_notebook_idempotence.py`

## Checks

Notebook must contain:

- environment check;
- input ZIP validation;
- resume logic;
- output ZIP creation;
- blocked status JSON;
- no certificate code;
- no paper evidence code;
- actual wall-time logging as `run_log_only`;
- GPU sharding logic.
