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

# V7 Prompt 15 — Final V7 Audit and Handoff

Implement final V7 audit that checks execution readiness, not paper readiness.

Create:

- `python -m certgen.audit.v7_execution_development_audit`;
- `docs/V7_EXECUTION_DEVELOPMENT_AUDIT.md`;
- `data/results/v7_execution_development_audit.json`;
- `docs/V7_SINGLE_FILE_HANDOFF.md`.

Audit checks:

- CIFAR reference onramps exist;
- generation bookrun notebook exists;
- feature extraction bookrun notebook exists;
- input ZIP builders exist;
- output ZIP importers/validators exist;
- run ledger exists;
- stage dashboard exists;
- scale lanes exist;
- notebook quality validator exists;
- paper result gate exists;
- no `claim_allowed=true`;
- no fake empirical results;
- no certificate run without gates;
- no FID certificate claim;
- exact current blocker is reported;
- exact next command is reported.

Final handoff must include:

- current status;
- exact next local CPU command;
- exact next Kaggle notebook step;
- what files to upload/download;
- expected runtimes;
- stop conditions;
- what not to build next.

Verification:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.v7_execution_development_audit --out docs/V7_EXECUTION_DEVELOPMENT_AUDIT.md --json-out data/results/v7_execution_development_audit.json
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.final_execution_audit --out docs/FINAL_EXECUTION_AUDIT.md --json-out data/results/final_execution_audit.json
```
