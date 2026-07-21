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

# V7 Prompt 09 — Certificate Pilot Expansion and Sensitivity

Upgrade the CPU certificate pilot while keeping it blocked until real features and sanity gates pass.

When ready, run only CPU:

- null calibration;
- reference-vs-corruption sanity;
- google DDPM vs Frank CFM;
- google DDPM vs Frank DDPM EMA;
- preprocessing sensitivity if available.

Metrics/certificates:

- bounded RBF-MMD on Inception features;
- bounded CLIP-MMD / CMMD on CLIP features;
- betting CS or valid bounded CS;
- block-size sensitivity;
- alpha sensitivity;
- sample-order/replay sensitivity.

Forbidden:

- rigorous FID certificate;
- certified polynomial KID by default;
- paper evidence promotion.

Outputs only if gates pass:

- `docs/V7_FIRST_PILOT_REPORT.md`;
- `data/results/v7_first_pilot_certificates/*.json`;
- `data/results/v7_first_pilot_undecided_fraction.json`;
- `docs/V7_FIRST_PILOT_LIMITATIONS.md`.

Labels:

- `pilot_only`;
- `single_benchmark_only`;
- `not_paper_evidence`;
- `not_generalized`;
- `claim_allowed=false`.

If gates do not pass, output exact blocker and create no certificate cards.
