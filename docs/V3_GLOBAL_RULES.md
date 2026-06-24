# CertGen V3 Global Rules

`NO_REAL_EVIDENCE`

V3 prepares CertGen for a first real pilot. It does not create paper evidence by itself.

Allowed V3 evidence statuses:

- `smoke_only`
- `synthetic_only`
- `dry_run_only`
- `planned_only`
- `real_features_unvalidated`
- `real_features_validated`
- `real_pilot_pending`
- `real_pilot_non_claim`
- `real_pilot_claim_blocked`
- `real_pilot_claim_eligible`

Only `real_pilot_claim_eligible` can ever support paper-facing empirical language. All other statuses must carry `claim_allowed: false`.

FID and FD-DINOv2 remain descriptive-only unless a later proof-backed implementation changes that policy.
