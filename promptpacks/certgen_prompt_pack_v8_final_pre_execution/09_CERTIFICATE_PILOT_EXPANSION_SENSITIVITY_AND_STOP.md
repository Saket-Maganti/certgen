# V8 Prompt 09 — Certificate Pilot Expansion, Sensitivity, and Stop


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

Prepare CPU certificate pilot expansion so it runs only after metric sanity gates pass.

## Build/upgrade

- `commands/v8_cpu_execution/11_run_certificate_pilot_if_ready.sh`
- `docs/V8_CERTIFICATE_PILOT_PROTOCOL.md`
- `data/results/v8_certificate_pilot_status.json`

## Pilot pairs

- null calibration reference split vs reference split;
- reference vs corruption sanity;
- google DDPM vs Frank CFM;
- google DDPM vs Frank DDPM EMA;
- preprocessing sensitivity if available.

## Metrics

- bounded RBF-MMD on Inception;
- bounded CMMD / CLIP-MMD;
- valid/betting CS;
- no FID certificate;
- no certified polynomial KID by default.

## Sensitivity

Include block-size sensitivity only from cached features and only CPU-side.

## Labels

Every output must be:

- `pilot_only`
- `not_paper_evidence`
- `single_benchmark_only`
- `not_generalized`
- `claim_allowed=false`
