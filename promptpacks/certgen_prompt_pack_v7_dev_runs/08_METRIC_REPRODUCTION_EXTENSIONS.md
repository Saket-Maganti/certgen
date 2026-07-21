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

# V7 Prompt 08 — Metric Reproduction and Sanity Extensions

Extend R1D so the first pilot can proceed even when no published point estimate is reproducible at 1k, while still staying honest.

Implement statuses:

- `PUBLISHED_METRIC_REPRODUCTION_PASSED`;
- `PUBLISHED_METRIC_REPRODUCTION_FAILED`;
- `PILOT_SANITY_ONLY_NO_PUBLISHED_METRIC_REPRODUCTION`;
- `BLOCKED_FEATURE_CACHE_INVALID`;
- `BLOCKED_REQUIRED_ROLE_MISSING`.

Add sanity checks:

- reference split-vs-split null calibration feasible;
- reference-vs-corruption obvious-gap sanity feasible;
- generated roles present;
- feature dims stable;
- sample counts adequate for 1k pilot;
- preprocessing lock hashes present;
- no feature NaN/inf;
- no duplicate sample IDs within role.

Outputs:

- `docs/V7_METRIC_SANITY_GATE_REPORT.md`;
- `data/results/v7_metric_sanity_gates.json`.

Do not fake reproduction. If no published metric is available for 1k, say exactly that and proceed only to `pilot_sanity_only` if permitted.
