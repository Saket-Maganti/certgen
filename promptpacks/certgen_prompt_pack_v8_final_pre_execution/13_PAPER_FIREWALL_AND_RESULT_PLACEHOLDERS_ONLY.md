# V8 Prompt 13 — Paper Firewall and Result Placeholders Only


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

Ensure no pilot-only or run-log-only output leaks into paper as a claim.

## Build/upgrade

- `certgen/paper/v8_result_firewall.py`
- `docs/V8_PAPER_FIREWALL_REPORT.md`
- `data/results/v8_paper_firewall.json`

## Requirements

Scan paper directories and block:

- fake empirical numbers;
- pilot-only numbers injected as general claims;
- `claim_allowed=true` without gates;
- FID certificate language;
- certified polynomial KID language.

Allow placeholders labeled `TBD_AFTER_REAL_RUNS`.
