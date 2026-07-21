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

# V7 Prompt 00 — Global Rules and Objective

Implement the V7 developmental execution upgrade pack.

V7 is allowed to add more run infrastructure only if it directly supports one of these:

1. unblocking CIFAR-10 reference materialization;
2. making Kaggle T4×2 generation notebooks easier and safer to run;
3. making Kaggle T4×2 feature-extraction notebooks easier and safer to run;
4. validating/copying back Kaggle outputs;
5. creating real run ledgers and current-stage dashboards;
6. supporting 1k → 10k → 50k scale lanes;
7. handling failures/retries/resume;
8. ensuring CPU-only certificate/statistical execution;
9. preventing evidence leakage and claim inflation.

Do not implement decorative docs. Every new file must have a clear execution role.

Required first action:

- Read existing V6 artifacts: `docs/V6_CPU_AND_KAGGLE_MASTER_EXECUTION_RUNBOOK.md`, `docs/FINAL_EXECUTION_AUDIT.md`, `commands/v6_cpu_execution/`, `notebooks/kaggle/`, `certgen/packaging/`, and `certgen/pipeline/v6_execution.py`.
- Produce `docs/V7_EXECUTION_UPGRADE_PLAN.md` with a short exact list of files and commands you will add.

Verification:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.final_execution_audit --out docs/FINAL_EXECUTION_AUDIT.md --json-out data/results/final_execution_audit.json
```

Final response must state current exact blocker. If still `BLOCKED_MISSING_REFERENCE_SAMPLES`, do not hide it.
