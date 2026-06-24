# CertGen V3 Single-File Handoff

`NO_REAL_EVIDENCE`

Project status after V3:

CertGen is real-pilot-ready in infrastructure terms. It can validate provenance, feature caches, metric reproduction, pilot configs, certificate replay, and no-claim reports.

Implemented modules:

- V3 status policy.
- Intake audit.
- Provenance ledger validator.
- Strict feature-cache validator.
- Feature extraction dry-run adapters.
- Metric reproduction audit.
- First-pilot orchestrator.
- Certificate replay.
- Pilot report cards.
- V3 registry and availability tables.
- V3 optional-stopping lab.
- V3 final audit.

Generated artifacts:

- V3 audit reports.
- Dry-run feature extraction plan.
- Provenance validation report.
- Optional-stopping synthetic diagnostic.
- Synthetic validated-cache pilot outputs.

Evidence boundary:

All V3 generated artifacts default to `claim_allowed: false`. No paper claim exists.

Current limitations:

- no real benchmark audit yet unless user has supplied validated real features;
- no decidedness fraction yet unless real pilot was run in validated mode;
- no ranking movement claim;
- FID/FD descriptive-only;
- first paper claim remains blocked until real gates pass.

Exact next V4 action:

Fill the provenance ledger for one benchmark/model-pair set, acquire or materialize real feature caches, validate them, reproduce one metric point estimate, and run the first clean-core pilot in non-claim mode.
