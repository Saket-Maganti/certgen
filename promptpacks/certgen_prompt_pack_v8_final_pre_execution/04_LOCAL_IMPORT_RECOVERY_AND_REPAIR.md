# V8 Prompt 04 — Local Import, Recovery, and Repair for Kaggle Outputs


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

Make local copy-back robust: generation ZIP and feature ZIP imports should validate, recover from common partial-output formats, and provide exact repair instructions.

## Build/upgrade

- `certgen/packaging/import_and_repair_generation_zip.py`
- `certgen/packaging/import_and_repair_feature_zip.py`
- `commands/v8_cpu_execution/05_import_generation_zip_repair.sh`
- `commands/v8_cpu_execution/06_import_feature_zip_repair.sh`
- `docs/V8_KAGGLE_OUTPUT_IMPORT_RECOVERY_GUIDE.md`

## Requirements

Generation import must detect:

- missing ZIP;
- missing model role;
- incomplete shard;
- duplicate seeds;
- duplicate paths;
- missing hashes;
- unexpected certificate/results files;
- `claim_allowed=true`.

Feature import must detect:

- missing feature role;
- missing sidecar;
- non-finite features;
- dimension mismatch;
- sample ID mismatch;
- duplicate IDs;
- role label mismatch;
- missing preprocessing/provenance hashes;
- unexpected paper/certificate outputs.

## Outputs

- repaired/extracted outputs under `data/sources/cifar10_r1/` and `data/features/cifar10_r1/`;
- summary JSON files;
- exact next command.

## Tests

Use fake tiny ZIPs to test good, missing-role, duplicate, and forbidden-file cases.
