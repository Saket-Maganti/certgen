# Prompt 01 — Bootstrap the CertGen Repository Scaffold

## Objective

Build the basic CertGen repository scaffold. This is the foundation only. Do not implement heavy feature extraction, real metric audits, or paper claims yet.

## Required context

Read:

- `CERTGEN_PROJECT_MASTER_CONTEXT.md`
- `00_GLOBAL_RULES_FOR_ALL_PROMPTS.md`

## Create the repository structure

Create a Python package named `certgen` with this structure:

```text
certgen/
  __init__.py
  cli/
    __init__.py
    validate_config.py
    make_smoke_artifacts.py
  core/
    __init__.py
    io.py
    hashing.py
    provenance.py
    enums.py
  schemas/
    __init__.py
    dataset.py
    model.py
    feature_manifest.py
    metric.py
    comparison.py
    certificate.py
    audit_record.py
  metrics/
    __init__.py
    fid.py
    mmd.py
    kid.py
    cmmd.py
    fd_dinov2.py
  certs/
    __init__.py
    confidence_sequence.py
    decision.py
    stopping.py
  gates/
    __init__.py
    claim_gate.py
    fid_policy_gate.py
    evidence_gate.py
  reporting/
    __init__.py
    certificate_report.py
    audit_summary.py
  pilots/
    __init__.py
    registry.py
    smoke_pilot.py
configs/
  certgen_v1_smoke.yaml
docs/
  CERTGEN_V1_README.md
  CLAIMS_POLICY.md
  FID_POLICY.md
  EVIDENCE_STATUS_POLICY.md
  RUNBOOK_V1.md
tests/
  test_imports.py
  test_smoke_config.py
  test_evidence_status.py
  test_claim_gate.py
  test_fid_policy_gate.py
  test_smoke_artifact_non_evidence.py
```

Also create:

```text
pyproject.toml
README.md
```

## Project metadata

Use sensible package metadata:

- name: `certgen`
- description: `Anytime-valid, metric-agnostic decision certificates for generative-model comparison`
- Python: `>=3.10`
- core dependencies: keep minimal
- test dependency: `pytest`

Do not require PyTorch, torchvision, transformers, timm, or CUDA in the base install. If referenced later, they must be optional extras.

## Basic CLI commands

Implement these two minimal commands:

```bash
python -m certgen.cli.validate_config --config configs/certgen_v1_smoke.yaml
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1
```

`validate_config` should:

- read YAML if PyYAML is available;
- otherwise support JSON fallback or fail with a clear message;
- validate required top-level fields;
- print a concise validation summary.

`make_smoke_artifacts` should:

- create tiny synthetic/non-evidence toy inputs;
- write a provenance JSON;
- write a clearly marked `non_evidence_smoke` artifact;
- not compute or claim any real model comparison.

## Required config fields

The V1 smoke config should include:

```yaml
project: CertGen
version: v1_smoke
mode: smoke
alpha: 0.05
max_samples: 128
metrics:
  - kid
  - cmmd
fid_policy: descriptive_only
allow_real_evidence: false
evidence_status: non_evidence_smoke
```

## Tests

Add tests that verify:

1. package imports;
2. smoke config validates;
3. smoke artifacts are marked `non_evidence_smoke`;
4. real evidence is not allowed in V1 smoke mode;
5. the FID policy is not accidentally treated as rigorous;
6. claim gate blocks words like `certified result`, `real evidence`, `published audit finding`, and `model A beats model B` in smoke reports.

## Acceptance criteria

Run:

```bash
python -m pytest -q
python -m certgen.cli.validate_config --config configs/certgen_v1_smoke.yaml
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1
```

A successful V1 bootstrap has no real data, no real claims, and all artifacts marked non-evidence.
