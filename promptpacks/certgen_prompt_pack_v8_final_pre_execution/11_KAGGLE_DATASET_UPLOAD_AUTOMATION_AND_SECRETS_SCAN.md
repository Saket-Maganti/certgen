# V8 Prompt 11 — Kaggle Dataset Upload Automation and Secrets Scan


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

Make Kaggle upload folders safe and repeatable.

## Build/upgrade

- `certgen/packaging/prepare_kaggle_upload_folder.py`
- `commands/v8_cpu_execution/12_prepare_kaggle_generation_upload_folder.sh`
- `commands/v8_cpu_execution/13_prepare_kaggle_feature_upload_folder.sh`
- `docs/V8_KAGGLE_UPLOAD_GUIDE.md`

## Requirements

Upload folder must include:

- input ZIP;
- README;
- manifest JSON;
- expected Kaggle dataset name;
- notebook name;
- no secrets/tokens;
- no paper evidence;
- `claim_allowed=false`.

Add secrets scan for common token patterns.
