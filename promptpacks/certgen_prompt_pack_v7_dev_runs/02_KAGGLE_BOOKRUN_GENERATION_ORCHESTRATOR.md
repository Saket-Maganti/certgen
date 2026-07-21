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

# V7 Prompt 02 — Kaggle T4×2 Generation Bookrun Orchestrator

Upgrade the generation notebook from a static notebook to a proper bookrun with status tracking, resumption, timed cells, and output validation.

Create or update:

- `notebooks/kaggle/v7_certgen_cifar10_generation_t4x2_bookrun.ipynb`
- `docs/V7_KAGGLE_GENERATION_BOOKRUN_GUIDE.md`
- `commands/v7_cpu_execution/02_create_generation_bookrun_zip.sh`

The notebook must include cells for:

1. mount/input discovery;
2. package checksum display;
3. dependency install;
4. environment snapshot;
5. T4×2 GPU visibility and memory check;
6. generation config validation;
7. per-model dry-run load check;
8. per-model two-GPU generation;
9. per-shard manifest write;
10. manifest merge;
11. duplicate seed/path/hash validation;
12. sample image grid preview saved as `run_log_only`;
13. timing summary;
14. output ZIP creation;
15. `generation_status.json` with exact status;
16. copy-back instructions.

Models:

- `google/ddpm-cifar10-32`;
- `FrankCCCCC/ddpm_ema_cifar10`;
- `FrankCCCCC/cfm-cifar10-32`.

Parallel strategy:

- GPU 0 seeds 0–499;
- GPU 1 seeds 500–999;
- no NCCL;
- no distributed training;
- simple independent processes.

The notebook must support:

- `SAMPLE_COUNT_PER_MODEL = 1000 | 10000 | 50000`;
- `RESUME = True`;
- `STOP_ON_FIRST_MODEL_FAILURE = True`;
- `WRITE_BLOCKED_STATUS_ON_FAILURE = True`.

If a checkpoint fails, write `generation_blocked_status.json` and stop. Do not generate partial success as if complete.

Runtime estimates must be included in markdown cells and labeled planning-only. Actual notebook timing must be labeled `run_log_only`.

Tests must parse the notebook JSON and confirm it contains:

- both GPU shard IDs;
- all three checkpoint IDs;
- output ZIP creation;
- blocked status behavior;
- no certificate code;
- no `claim_allowed=true`.
