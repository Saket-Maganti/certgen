# V1 Schema and Gate Report

Implemented:

- Evidence, metric-family, certificate-status, and FID-rigor enums.
- Dataclass schemas for datasets, models, features, metrics, comparisons, certificates, and audit claims.
- Deterministic JSON hashing.
- Evidence gate for smoke mode.
- Claim gate for generated non-evidence reports.

Blocked:

- `real_evidence_candidate` in smoke mode.
- Forbidden claim wording in generated non-evidence reports.

Still planned:

- Real-data evidence promotion gates.
- Full audit ingestion validation.
