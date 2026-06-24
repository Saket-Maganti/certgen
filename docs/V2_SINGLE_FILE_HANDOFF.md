# CertGen V2 Single-File Handoff

`NO_REAL_EVIDENCE`

V1 starting point:

- V1 audit passed.
- V1 had scaffolds, smoke artifacts, registry templates, claim gates, and descriptive-only FID policy.

V2 implemented:

- Clean MMD/KID/CMMD contribution streams.
- Bounded confidence-sequence implementations.
- Clean metric certificate API and CLI.
- Synthetic optional-stopping lab.
- Synthetic fixture generator.
- Feature-cache schema and validator.
- Registry V2 templates and validation.
- Dry-run first-pilot planner.
- FID policy reinforcement.
- Certificate-card reporting.
- V2 final audit.

Test command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Commands added:

- `python -m certgen.cli.certify_clean_metric ...`
- `python -m certgen.experiments.optional_stopping_lab ...`
- `python -m certgen.fixtures.make_v2_feature_fixtures ...`
- `python -m certgen.cli.validate_feature_cache ...`
- `python -m certgen.cli.plan_first_pilot_v2 ... --dry-run`
- `python -m certgen.cli.check_fid_policy ...`
- `python -m certgen.cli.render_certificate_card ...`
- `python -m certgen.cli.v2_audit ...`

Still non-evidence:

- All synthetic fixtures.
- All smoke certificates.
- Optional-stopping lab outputs.
- Dry-run pilot plans.

FID policy:

FID and FD-DINOv2 remain descriptive-only in V2.

Exact next V3 action:

Select one verified public/free benchmark row, validate real feature caches, and run the first clean-core pilot after provenance gates pass.

V3 go/no-go number:

First-benchmark undecided fraction.
