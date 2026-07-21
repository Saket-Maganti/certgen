# V8 Prompt 07 — Checkpoint Adapter Real-Load Preflight


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

Before burning full Kaggle sessions, add a Kaggle mini-preflight notebook/cell that loads each checkpoint and generates 1–4 images only.

## Artifacts

- `notebooks/kaggle/v8_checkpoint_preflight_t4x2.ipynb`
- `docs/V8_CHECKPOINT_PREFLIGHT_GUIDE.md`
- `data/results/v8_checkpoint_preflight_schema.json`

## Requirements

The preflight notebook must:

- install deps;
- load each checkpoint:
  - `google/ddpm-cifar10-32`
  - `FrankCCCCC/ddpm_ema_cifar10`
  - `FrankCCCCC/cfm-cifar10-32`
- generate 1–4 images/model;
- record actual loader class/scheduler;
- record wall time;
- write `preflight_status.json`;
- output `certgen_checkpoint_preflight_outputs.zip`;
- not count as empirical result or paper evidence.

If a checkpoint fails, write a blocked status and exact failure.
