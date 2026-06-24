# V2 Clean Metric Certificate API

`NO_REAL_EVIDENCE`

Example:

```bash
python3 -m certgen.cli.certify_clean_metric --features-a data/smoke/v2/features/model_a_close.npz --features-b data/smoke/v2/features/model_b_far.npz --features-r data/smoke/v2/features/reference.npz --metric kid_polynomial --comparison-id smoke_pair_001 --alpha 0.05 --budget-units 32 --clip-lower -5 --clip-upper 5 --out data/smoke/v2/certificates/smoke_pair_001_kid_certificate.json --evidence-status smoke_only
```

The output certificate includes feature hashes, stream hash, method label, theory status, bounds metadata, and `claim_allowed: false`.
