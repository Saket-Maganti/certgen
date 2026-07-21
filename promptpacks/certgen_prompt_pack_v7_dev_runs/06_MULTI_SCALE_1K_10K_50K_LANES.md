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

# V7 Prompt 06 — Multi-Scale 1k/10k/50k Lanes

Build controlled scale lanes. Do not run them automatically.

Create:

- `configs/v7_scale_lanes/cifar10_1k.yaml`;
- `configs/v7_scale_lanes/cifar10_10k.yaml`;
- `configs/v7_scale_lanes/cifar10_50k.yaml`;
- `commands/v7_cpu_execution/07_prepare_10k_generation_zip_if_1k_passed.sh`;
- `commands/v7_cpu_execution/08_prepare_50k_generation_zip_if_10k_passed.sh`;
- `docs/V7_SCALE_LANES_1K_10K_50K.md`.

Escalation gates:

1k → 10k only if:

- reference materialized;
- 1k generation complete;
- 1k feature extraction complete;
- CPU feature validation passes;
- metric/sanity gates pass;
- no fake evidence;
- final audit permits scale.

10k → 50k only if:

- 10k generation and features validate;
- runtime fits free Kaggle budget;
- no source/license blockers;
- first pilot results justify scale.

Runtime estimates:

- generation 1k/model: ~10–60 min/model;
- generation 10k/model: ~1–8 hr/model;
- generation 50k/model: ~6–24+ hr/model;
- feature extraction 1k/model+reference: Inception ~5–30 min, CLIP ~10–45 min;
- feature extraction 10k/model: Inception ~10–60 min, CLIP ~30–120 min;
- feature extraction 50k/model: Inception ~30–180 min, CLIP ~1–6 hr.

All estimates planning-only unless measured, and measured notebook times are `run_log_only`.
