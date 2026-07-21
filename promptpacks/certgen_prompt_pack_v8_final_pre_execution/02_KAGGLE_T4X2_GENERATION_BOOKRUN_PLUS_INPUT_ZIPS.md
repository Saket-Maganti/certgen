# V8 Prompt 02 — Kaggle T4x2 Generation Bookrun + Input ZIP Hardening


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

Upgrade the generation bookrun so it is robust enough for real use on Kaggle T4x2, with input ZIP validation, resume, measured run logs, and clear failure states.

## Upgrade artifacts

- `notebooks/kaggle/v8_certgen_cifar10_generation_t4x2_bookrun.ipynb`
- `docs/V8_KAGGLE_GENERATION_BOOKRUN_GUIDE.md`
- `commands/v8_cpu_execution/02_prepare_generation_bookrun_zip.sh`
- `certgen/packaging/build_v8_generation_input_zip.py` or compatible CLI wrapper
- `data/results/v8_generation_input_zip_manifest.json`

## Notebook requirements

Notebook must:

1. Check GPU count/names, CUDA, disk, Python, package versions.
2. Unzip input package.
3. Validate checkpoint list and seed plan.
4. Generate 1k/model by default:
   - GPU0 seeds 0-499;
   - GPU1 seeds 500-999.
5. Support 10k and 50k modes via config only, not copy-pasted notebooks.
6. Resume partial shards.
7. Write per-shard manifests and run logs.
8. Write `generation_blocked_status.json` if any checkpoint fails.
9. Merge manifests deterministically.
10. Output `/kaggle/working/certgen_cifar10_generation_outputs.zip`.
11. Never run feature extraction/certificates/paper evidence.

## Estimated runtimes doc

Update/create `docs/V8_GENERATION_RUNTIME_ESTIMATES.md` with:

- 1k/model: ~30 min–3 hr total for all 3 models on T4x2;
- 10k/model: ~3–24 hr total depending model speed;
- 50k/model: may require multiple sessions, ~18–72+ hr total.

Label planning estimates unless measured.

## Tests

Tests must inspect notebook JSON for:

- T4x2 sharding;
- output ZIP creation;
- failure JSON;
- no certificate/paper evidence cells.
