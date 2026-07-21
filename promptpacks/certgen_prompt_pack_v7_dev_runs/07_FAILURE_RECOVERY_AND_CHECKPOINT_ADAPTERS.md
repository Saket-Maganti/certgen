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

# V7 Prompt 07 — Failure Recovery and Checkpoint Adapter Hardening

Improve generation adapter reliability without claiming results.

Targets:

- `google/ddpm-cifar10-32`;
- `FrankCCCCC/ddpm_ema_cifar10`;
- `FrankCCCCC/cfm-cifar10-32`.

Implement:

- adapter preflight load checks;
- model-card-compatible scheduler detection;
- explicit failure statuses;
- retry policy for transient download errors;
- resume-safe seed handling;
- per-model blocked status;
- no partial success as complete.

Create:

- `certgen/generation/checkpoint_adapters.py`;
- `python -m certgen.generation.preflight_check_cifar10_checkpoints`;
- `docs/V7_CHECKPOINT_ADAPTER_FAILURE_PLAYBOOK.md`;
- `data/results/v7_checkpoint_preflight_status.json` when run.

Do not run internet/model downloads in tests. Mock adapters in tests.

Kaggle notebook should call preflight before generation and stop on failure.
