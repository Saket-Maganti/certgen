# V8 Prompt 01 — God-Tier CIFAR-10 Reference Onramp


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

Eliminate the recurring `BLOCKED_MISSING_REFERENCE_SAMPLES` blocker as much as possible without faking data.

## Build

Create or upgrade:

- `certgen/data/cifar10_onramp.py`
- `commands/v8_cpu_execution/01_cifar10_onramp.sh`
- `docs/V8_CIFAR10_ONRAMP_GUIDE.md`
- `data/results/v8_cifar10_onramp_status.json`

## Supported input modes

The onramp must support all of these, in priority order:

1. `CIFAR_ROOT=/path/to/image/tree`
2. `CIFAR_ARCHIVE_ROOT=/path/to/extracted/cifar-10-batches-py/or/parent`
3. `CIFAR_SEARCH_ROOT=/path/to/search` autodetect
4. `TORCHVISION_CIFAR_ROOT=/path/to/cache` existing cache only
5. Explicit user-approved download mode:
   - allowed only with `--allow-download` or `ALLOW_CIFAR_DOWNLOAD=1`
   - never in tests
   - report source URL and hash summary.

## Requirements

The CLI must:

- detect CIFAR-10 image trees and official archive layouts;
- materialize 32x32 RGB images where needed;
- write `registry/manifests/cifar10_r1_reference.jsonl`;
- write `data/results/v8_cifar10_reference_summary.json`;
- validate expected split counts when the source is complete;
- support pilot-only smaller references if explicitly requested, labeled `pilot_reference_subset_only`;
- preserve `claim_allowed=false`;
- label license unresolved as `license_unknown_reference_only`;
- block paper evidence while license is unresolved.

## Tests

Tests must use tiny fake fixtures only. No internet, no torchvision download, no Kaggle.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
bash commands/v8_cpu_execution/01_cifar10_onramp.sh || true
python3 -m certgen.audit.final_execution_audit --out docs/FINAL_EXECUTION_AUDIT.md --json-out data/results/final_execution_audit.json
```

## Final response must report

- whether CIFAR reference is materialized;
- exact manifest path;
- sample count;
- exact blocker if still missing;
- next command.
