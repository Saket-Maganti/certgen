# Command Index V1

```bash
python -m certgen.cli.validate_config --config configs/certgen_v1_smoke.yaml
```

Validate the V1 smoke config. Evidence status: `non_evidence_smoke`.

```bash
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1
```

Create smoke artifacts without metrics. Evidence status: `non_evidence_smoke`.

```bash
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics --make-certificate
```

Create toy metric outputs and a smoke certificate. Evidence status: `non_evidence_smoke`.

```bash
python -m certgen.cli.validate_registry --benchmarks registry/candidate_benchmarks_template.csv --pairs registry/candidate_model_pairs_template.csv
```

Validate pilot registry templates. Evidence status: `non_evidence_planned`.

```bash
python -m certgen.cli.plan_first_pilot --pairs registry/candidate_model_pairs_template.csv --out docs/FIRST_PILOT_PLAN.md
```

Generate a first-pilot TODO plan. Evidence status: `non_evidence_planned`.

```bash
python -m certgen.cli.v1_audit --out docs/V1_FINAL_AUDIT.md --json-out data/results/v1_final_audit.json
```

Run the final V1 audit. Evidence status: `non_evidence_smoke`.

```bash
python -m certgen.features.extract_inception --dry-run
python -m certgen.features.extract_clip --dry-run
python -m certgen.features.extract_dinov2 --dry-run
```

Dry-run feature-extraction stubs. Evidence status: no output by default.
