# Reproducibility Capsule V5

`NO_REAL_EVIDENCE`

Install and test:

```bash
python3 -m pip install -e .[test]
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Expected pre-run outputs are smoke, synthetic, dry-run, or template artifacts with `claim_allowed=false`.

Real-run template flow:

1. Validate state and claim boundaries.
2. Validate a real provenance ledger.
3. Validate or materialize feature caches.
4. Lock preprocessing.
5. Reproduce one reported metric point estimate.
6. Run the first clean-core pilot in non-claim mode.
7. Render the report card.
8. Run the V5 final audit.

