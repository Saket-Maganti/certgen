# V8 Prompt 06 — Multi-Scale 1k/10k/50k Lanes and Budget Gates


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

Create scale lanes that prevent wasteful 10k/50k runs until 1k gates pass.

## Build/upgrade

- `configs/v8_scale_lanes/cifar10_1k.yaml`
- `configs/v8_scale_lanes/cifar10_10k.yaml`
- `configs/v8_scale_lanes/cifar10_50k.yaml`
- `commands/v8_cpu_execution/08_prepare_10k_if_1k_passed.sh`
- `commands/v8_cpu_execution/09_prepare_50k_if_10k_passed.sh`
- `docs/V8_SCALE_LANES_AND_BUDGET_GATES.md`

## Gate rules

10k is allowed only if:

- reference materialized;
- 1k generation imported;
- 1k feature extraction imported;
- metric sanity gates pass;
- no forbidden claim artifacts;
- dashboard marks 1k as completed or ready to scale.

50k is allowed only if 10k passes the same gates.

## Runtime estimates

Include Kaggle hours and local CPU times for each lane.
