# V8 Prompt 15 — Final V8 Audit and Handoff


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

Implement and run a final audit that says whether the repo is ready for real execution or blocked only by user-provided CIFAR data.

## Build

- `certgen/audit/v8_final_pre_execution_audit.py`
- `docs/V8_FINAL_PRE_EXECUTION_AUDIT.md`
- `data/results/v8_final_pre_execution_audit.json`
- `docs/V8_SINGLE_FILE_HANDOFF.md`

## Audit checks

- CIFAR onramp exists;
- generation bookrun exists;
- feature bookrun exists;
- input ZIP builders exist;
- output importers exist;
- run ledger/dashboard exists;
- notebook idempotence passes;
- paper firewall passes;
- final execution audit status is honest;
- no fake results;
- no `claim_allowed=true`;
- no certificates unless gates passed;
- no feature extraction unless package validated.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.v8_final_pre_execution_audit --out docs/V8_FINAL_PRE_EXECUTION_AUDIT.md --json-out data/results/v8_final_pre_execution_audit.json
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.final_execution_audit --out docs/FINAL_EXECUTION_AUDIT.md --json-out data/results/final_execution_audit.json
```

## Final statuses

The audit must return one of:

- `READY_FOR_REAL_EXECUTION`
- `READY_FOR_KAGGLE_GENERATION`
- `BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE`
- `BLOCKED_REPO_INCONSISTENT`

Final response must include exact next command.
