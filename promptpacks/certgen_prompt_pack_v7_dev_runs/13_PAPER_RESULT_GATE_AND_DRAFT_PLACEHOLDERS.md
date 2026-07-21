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

# V7 Prompt 13 — Paper Result Gate and Draft Placeholders

This prompt is not paper polish. It prevents accidental leakage of pilot-only or missing results into the paper.

Create:

- `python -m certgen.paper.audit_result_injection_gate`;
- `docs/V7_PAPER_RESULT_GATE_REPORT.md`;
- optional placeholder tables with `TBD_AWAITING_REAL_RUNS`, not numbers.

Audit must fail if:

- paper contains pilot-only numbers without labels;
- paper contains fake undecided fraction;
- paper claims FID certificate;
- paper claims CVPR-ready empirical results before real gates;
- paper references smoke/template results as evidence.

It may allow:

- method description;
- claim-gate description;
- execution runbook references;
- placeholders clearly labeled `TBD_AWAITING_REAL_RUNS`.

Do not rewrite the whole paper. This is a safety gate only.
