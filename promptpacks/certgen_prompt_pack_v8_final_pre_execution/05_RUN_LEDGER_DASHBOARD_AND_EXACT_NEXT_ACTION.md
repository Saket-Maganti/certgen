# V8 Prompt 05 — Run Ledger, Dashboard, and Exact Next Action


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

Make it impossible to lose track of the current stage. Every run should write to a JSONL ledger and render a dashboard with the exact next command.

## Upgrade

- `certgen/runledger/` existing modules;
- `docs/V8_EXECUTION_DASHBOARD.md`;
- `data/results/v8_run_ledger.jsonl`;
- `commands/v8_cpu_execution/07_render_dashboard.sh`.

## Required dashboard stages

- `missing_reference`
- `reference_ready`
- `generation_input_zip_ready`
- `generation_bookrun_pending`
- `generation_zip_imported`
- `feature_input_zip_ready`
- `feature_bookrun_pending`
- `feature_zip_imported`
- `metric_sanity_ready`
- `certificate_pilot_ready`
- `pilot_completed_no_claim`

Each stage must contain:

- status;
- exact next command;
- expected input path;
- expected output path;
- whether CPU/GPU;
- estimated runtime;
- claim status.
