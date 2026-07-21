# V8 Prompt 08 — Metric Sanity, Reproduction, and No-Fake-Reproduction Gate


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

Make the metric sanity stage useful even before a full published metric reproduction is possible.

## Build/upgrade

- `certgen/metrics/sanity_gate.py`
- `commands/v8_cpu_execution/10_run_metric_sanity.sh`
- `docs/V8_METRIC_SANITY_AND_REPRODUCTION_GUIDE.md`
- `data/results/v8_metric_sanity.json`

## Gate outputs

Possible statuses:

- `BLOCKED_FEATURE_CACHE_MISSING`
- `BLOCKED_FEATURE_CACHE_INVALID`
- `PILOT_SANITY_ONLY_NO_PUBLISHED_METRIC_REPRODUCTION`
- `PUBLISHED_METRIC_REPRODUCTION_PASSED`
- `PUBLISHED_METRIC_REPRODUCTION_FAILED`

## Checks

- Inception caches present/dim stable;
- CLIP caches present/dim stable;
- no NaNs/infs;
- null calibration feasible;
- obvious-gap sanity feasible;
- bounded RBF-MMD stream can be built;
- bounded CMMD stream can be built;
- KID-poly and FID remain descriptive.

Do not fabricate published metric reproduction. If no published metric can be reproduced at 1k, say so.
