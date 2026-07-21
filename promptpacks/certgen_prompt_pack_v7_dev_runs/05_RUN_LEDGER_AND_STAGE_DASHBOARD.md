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

# V7 Prompt 05 — Run Ledger and Stage Dashboard

Add a real execution ledger so the project always knows exactly where it is blocked.

Create:

- `certgen/runledger/ledger.py`;
- `python -m certgen.runledger.update_stage`;
- `python -m certgen.runledger.render_dashboard`;
- `data/results/v7_run_ledger.jsonl`;
- `docs/V7_EXECUTION_DASHBOARD.md`;
- `commands/v7_cpu_execution/06_render_execution_dashboard.sh`.

Ledger event schema:

- timestamp;
- stage;
- command;
- status;
- inputs;
- outputs;
- hashes where feasible;
- blocker code;
- claim_allowed;
- evidence_status;
- run_log_only flag;
- notes.

Dashboard must display:

- current blocker;
- next exact command;
- last successful CPU stage;
- last successful Kaggle stage;
- whether generation input ZIP exists;
- whether generation output ZIP exists;
- whether feature input ZIP exists;
- whether feature output ZIP exists;
- whether metric gates passed;
- whether first pilot ran;
- no fake evidence status.

Do not require a database. JSONL is enough.

Tests must verify stage transitions and no `claim_allowed=true` in ledger events.
