# V8 Prompt 03 — Kaggle T4x2 Feature Extraction Bookrun + Role Cache Hardening


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

Upgrade the feature extraction bookrun so Inception and CLIP caches are created, merged, sidecar-compatible, role-split-ready, and copy-back-safe.

## Upgrade artifacts

- `notebooks/kaggle/v8_certgen_cifar10_feature_extraction_t4x2_bookrun.ipynb`
- `docs/V8_KAGGLE_FEATURE_EXTRACTION_BOOKRUN_GUIDE.md`
- `commands/v8_cpu_execution/03_prepare_feature_bookrun_zip.sh`
- `commands/v8_cpu_execution/04_import_feature_bookrun_zip.sh`
- feature extraction runtime estimates.

## Notebook requirements

Notebook must:

1. Validate reference/generated sample package before loading models.
2. Extract Inception features with GPU0/GPU1 sharding.
3. Extract CLIP features with GPU0/GPU1 sharding.
4. Merge shards deterministically by `sample_id`.
5. Produce sidecar JSON with:
   - extractor name/version;
   - sample manifest hash;
   - preprocessing lock hash;
   - provenance hash;
   - role labels;
   - shard IDs;
   - device info;
   - `claim_allowed=false`.
6. Split role caches or write merge output compatible with local `split_by_role.py`.
7. Output `/kaggle/working/certgen_cifar10_features_outputs.zip`.
8. Never run certificates, metric claims, or paper evidence.

## Estimated runtime doc

Create/update `docs/V8_FEATURE_EXTRACTION_RUNTIME_ESTIMATES.md`:

- 1k/model + reference: Inception ~5–30 min, CLIP ~10–45 min;
- 10k/model: Inception ~10–60 min, CLIP ~30–120 min;
- 50k/model: Inception ~30–180 min, CLIP ~1–6 hr.

Label estimates as planning only.
