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

# V7 Prompt 14 — DevOps Cleanup, Git Snapshot, and Archive Hygiene

The repo has many generated artifacts. Add safe cleanup and snapshot commands.

Implement:

- `commands/v7_cpu_execution/11_repo_health_snapshot.sh`;
- `commands/v7_cpu_execution/12_archive_prompt_packs_and_old_reports.sh`;
- `docs/V7_REPO_HEALTH_AND_ARCHIVE_REPORT.md`;
- `.gitignore` improvements if needed.

Rules:

- Do not delete user work without explicit backup.
- Archive old prompt packs/reports under `archive/` only if safe.
- Do not remove evidence/provenance artifacts.
- Do not run `git commit` unless user explicitly asks.
- If git is not initialized, recommend `git init` and generate instructions; do not silently rewrite history.

Report:

- file count;
- dirty paths;
- large files;
- Kaggle inputs/outputs;
- generated artifacts;
- suggested archival action.
