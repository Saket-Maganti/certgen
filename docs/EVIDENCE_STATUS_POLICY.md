# Evidence Status Policy

Every CertGen artifact must carry one evidence status:

- `real_evidence_candidate`
- `non_evidence_smoke`
- `non_evidence_mock`
- `non_evidence_synthetic`
- `non_evidence_planned`
- `descriptive_only`

V1 smoke mode may generate only non-evidence or descriptive-only artifacts. `real_evidence_candidate` is blocked in smoke mode.
