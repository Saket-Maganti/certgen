# V8 Prompt 00 — Global Rules and Final Stop Condition


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

Create `docs/V8_FINAL_PRE_EXECUTION_PLAN.md` and update the execution dashboard to make the remaining path brutally explicit.

## Tasks

1. Read current state from:
   - `docs/FINAL_EXECUTION_AUDIT.md`
   - `docs/V7_EXECUTION_DEVELOPMENT_AUDIT.md`
   - `docs/V7_SINGLE_FILE_HANDOFF.md`
   - `docs/V6_CPU_AND_KAGGLE_MASTER_EXECUTION_RUNBOOK.md`
   - existing V7 command bundles and notebooks.
2. Confirm the current blocker chain.
3. Write `docs/V8_FINAL_PRE_EXECUTION_PLAN.md` with:
   - what is already built;
   - what is still missing;
   - exact post-V8 execution sequence;
   - hard stop rule: no V9 / no more scaffolding.
4. Add a machine-readable status file:
   - `data/results/v8_final_pre_execution_plan.json`.
5. Run baseline verification:
   - `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q`
   - final execution audit.

## Required final status

The report must state one of:

- `V8_READY_TO_HARDEN`
- `V8_BLOCKED_REPO_STATE_UNKNOWN`

Do not run real generation, feature extraction, or certificates.
