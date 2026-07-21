You are working on CertGen in `/Users/saketmaganti/Projects/certGen` after V6.

Global non-negotiables:
- Do not fabricate results.
- Do not create `claim_allowed=true` unless a specific real-evidence gate later permits it; for V7, keep `claim_allowed=false`.
- Do not use smoke/template/synthetic outputs as real evidence.
- Do not run certificates unless real feature caches and metric/sanity gates pass.
- Do not claim rigorous FID certification. FID remains descriptive-only.
- Polynomial KID remains descriptive/non-certified by default unless a separate valid bounded/nonasymptotic justification is implemented and audited.
- Rigorous certificate path remains bounded RBF-MMD / bounded CMMD / valid bounded streams.
- Kaggle T4×2 is for sample generation and feature extraction only. CPU/local is for validation, packaging, metric reproduction, certificates, reports, and audits.
- Every output must clearly label whether it is `NO_REAL_EVIDENCE`, `pilot_only`, `not_paper_evidence`, or `run_log_only`.
- Do not build generic V7 fluff. Build execution leverage: commands, notebooks, validators, packaging, recovery, and run lanes that get the first real pilot unstuck and scalable.

# V7 Prompt 03 — Kaggle T4×2 Feature Extraction Bookrun Orchestrator

Upgrade feature extraction into a robust Kaggle bookrun.

Create/update:

- `notebooks/kaggle/v7_certgen_cifar10_feature_extraction_t4x2_bookrun.ipynb`
- `docs/V7_KAGGLE_FEATURE_EXTRACTION_BOOKRUN_GUIDE.md`
- `commands/v7_cpu_execution/03_create_feature_bookrun_zip.sh`

Notebook must include:

1. input package discovery;
2. checksum and manifest validation;
3. GPU and disk check;
4. dependency install;
5. reference/generated sample count validation;
6. preprocessing-lock validation;
7. Inception extraction with shard 0/2 and shard 1/2;
8. CLIP extraction with shard 0/2 and shard 1/2;
9. deterministic shard merge;
10. feature sidecar generation;
11. role-aware split cache generation if feasible;
12. feature finite/dim/sample-id validation;
13. timing summary;
14. output ZIP creation;
15. copy-back instructions.

It must not run metrics, certificates, paper reports, or undecided fraction.

Output ZIP:

`/kaggle/working/certgen_cifar10_features_1k_outputs.zip`

Required roles:

- reference;
- google_ddpm;
- frank_ddpm_ema;
- frank_cfm.

Required feature families:

- inception;
- clip.

Optional:

- DINOv2 only if lightweight and clearly descriptive-only. Do not make DINO required for first pilot.

Runtime estimates:

- 1k/model plus reference: Inception ~5–30 min, CLIP ~10–45 min;
- 10k/model: Inception ~10–60 min, CLIP ~30–120 min;
- 50k/model: Inception ~30–180 min, CLIP ~1–6 hr.

Actual notebook timings are `run_log_only`, not evidence.

Tests must parse notebook JSON for GPU sharding, output ZIP, feature role labels, no certificates, no paper evidence.
