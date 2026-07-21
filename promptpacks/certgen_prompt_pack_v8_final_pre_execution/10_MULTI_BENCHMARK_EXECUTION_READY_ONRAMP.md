# V8 Prompt 10 — Multi-Benchmark Execution-Ready Onramp


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

Plan future benchmarks without distracting from CIFAR. This should produce a candidate table only, not execute multibench runs.

## Candidate benchmarks

- FFHQ/CelebA-HQ if released samples are easy;
- ImageNet 64/128/256 only if sample sets are available;
- LSUN only if provenance/license is easy;
- optional video only after image core succeeds.

## Deliverables

- `registry/provenance/v8_multibench_candidate_sources.csv`
- `docs/V8_MULTIBENCH_EXECUTION_ONRAMP.md`
- validator with statuses:
  - `candidate_ready_later`
  - `blocked_license`
  - `blocked_samples_unavailable`
  - `blocked_too_heavy`

No real runs. No paper claims.
