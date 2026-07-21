# V8 Prompt 14 — DevOps Safe Snapshot and Dirty Worktree Triage


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

Clean up operational risk without destructive changes.

## Build/upgrade

- `commands/v8_cpu_execution/14_repo_health_snapshot.sh`
- `commands/v8_cpu_execution/15_make_safe_archive_snapshot.sh`
- `docs/V8_REPO_HEALTH_SNAPSHOT.md`

## Requirements

Report:

- git status;
- dirty file count;
- large file candidates;
- prompt-pack archive candidates;
- generated result files;
- data files that should not be committed;
- exact backup/archive commands.

Do not move/delete files without explicit user approval.
