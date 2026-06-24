# Command Index V2

`NO_REAL_EVIDENCE`

```bash
python3 -m certgen.fixtures.make_v2_feature_fixtures --out-dir data/smoke/v2/features --seed 0
```

Generate deterministic synthetic smoke feature fixtures.

```bash
python3 -m certgen.cli.certify_clean_metric --features-a data/smoke/v2/features/model_a_close.npz --features-b data/smoke/v2/features/model_b_far.npz --features-r data/smoke/v2/features/reference.npz --metric kid_polynomial --comparison-id smoke_pair_001 --alpha 0.05 --budget-units 40 --clip-lower -1 --clip-upper 1 --method hoeffding --out data/smoke/v2/certificates/smoke_pair_001_kid_certificate.json --evidence-status smoke_only
```

Create a V2 clean-core smoke certificate.

```bash
python3 -m certgen.experiments.optional_stopping_lab --out-dir data/results/v2_optional_stopping_lab --num-replicates 50 --budget 80 --alpha 0.05 --seed 0 --evidence-status smoke_only
```

Run the synthetic optional-stopping smoke lab.

```bash
python3 -m certgen.cli.validate_feature_cache --manifest registry/feature_caches/smoke_feature_cache_manifest.json
```

Validate a feature-cache manifest.

```bash
python3 -m certgen.cli.plan_first_pilot_v2 --registry-dir registry --out-json data/results/v2_first_pilot_plan.json --out-md docs/V2_FIRST_PILOT_PLAN.md --dry-run
```

Create a dry-run-only first-pilot plan.

```bash
python3 -m certgen.cli.check_fid_policy --certificate data/smoke/v2/certificates/smoke_pair_001_kid_certificate.json
```

Check that a certificate does not violate the V2 FID/FD policy.

```bash
python3 -m certgen.cli.render_certificate_card --certificate data/smoke/v2/certificates/smoke_pair_001_kid_certificate.json --out docs/SMOKE_CERTIFICATE_CARD.md
```

Render a conservative certificate card.

```bash
python3 -m certgen.cli.v2_audit --out docs/V2_FINAL_AUDIT.md --json-out data/results/v2_final_audit.json
```

Run the V2 final audit.
