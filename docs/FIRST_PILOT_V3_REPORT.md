# Pilot Report Card V3

REAL_FEATURES_USED_IN_NON_CLAIM_MODE. Results may be used for debugging and go/no-go planning only.

This artifact is not paper evidence and must not be used to claim a decidedness fraction, ranking movement, model superiority, or published-result error.

- Pilot ID: `smoke_pilot_v3`
- Mode: `real_features`
- Evidence status: `real_pilot_non_claim`
- Claim allowed: `False`
- Blockers: `['V3 pilot defaults to non-claim mode']`
- Pilot result computed: `True`
- Undecided fraction: `1.0`

## Benchmark/Model Pair Table
- `smoke_a_vs_b`: `{'comparison_id': 'smoke_a_vs_b', 'feature_cache_valid': True}`

## Certificate Summary
- `{'path': 'data/results/first_pilot_v3/certificates/smoke_a_vs_b_mmd_rbf.json', 'decision': 'not_decided_at_budget', 'metric': 'mmd_rbf'}`

## FID/FD Descriptive-Only Section

FID and FD-DINOv2 remain descriptive-only unless a future rigorous method is established.

## Reproducibility Checklist

- Provenance ledger checked.
- Feature caches validated when present.
- Certificate replay available.

## Exact Commands

- `python -m certgen.cli.run_first_pilot ...`

## Forbidden Interpretations

- No model superiority claim.
- No ranking movement claim.
- No published-result error claim.
