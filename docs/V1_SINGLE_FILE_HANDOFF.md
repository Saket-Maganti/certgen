# CertGen V1 Single-File Handoff

CertGen is a metric-agnostic decision-certificate layer for generative-model comparison. It asks when one model is better than another under a chosen metric while preserving optional-stopping validity.

What V1 built:

- Python package scaffold.
- Schemas and evidence-status gates.
- Claim gate for generated non-evidence reports.
- Local feature-cache contracts.
- CPU toy MMD/KID/CMMD metrics.
- Descriptive FID and FD-DINOv2 handling.
- Clean-core smoke certificate scaffold.
- Pilot registry templates.
- Reporting and reproducibility docs.
- Final V1 audit command.

What V1 did not build:

- Real feature extraction runs.
- Real benchmark/model audit.
- Real decidedness fraction.
- Real leaderboard movement analysis.
- Final paper text.
- Verified BibTeX.

Commands:

```bash
python -m pytest -q
python -m certgen.cli.validate_config --config configs/certgen_v1_smoke.yaml
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics --make-certificate
python -m certgen.cli.validate_registry --benchmarks registry/candidate_benchmarks_template.csv --pairs registry/candidate_model_pairs_template.csv
python -m certgen.cli.plan_first_pilot --pairs registry/candidate_model_pairs_template.csv --out docs/FIRST_PILOT_PLAN.md
python -m certgen.cli.v1_audit --out docs/V1_FINAL_AUDIT.md --json-out data/results/v1_final_audit.json
```

Evidence policy:

V1 smoke mode generates only `non_evidence_smoke`, `non_evidence_planned`, or `descriptive_only` artifacts.

FID limitation:

FID is descriptive-only in V1. A clean optional-stopping certificate is available only for clean MMD/KID/CMMD-style paths.

Next step for V2:

Replace or refine the V1 interval scaffold with the final clean-core confidence-sequence/e-process implementation, then dry-run feature extraction for one verified benchmark.

First-pilot go/no-go number:

The fraction of contestable first-benchmark reported gaps that are not decided under the certificate at the relevant sample size.

Current status:

No real results exist.
