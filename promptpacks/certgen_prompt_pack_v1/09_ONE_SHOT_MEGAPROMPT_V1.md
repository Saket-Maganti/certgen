# CertGen V1 One-Shot Megaprompt

Use this only if you want one implementation agent to build the entire V1 basics in one session.

---

You are implementing **CertGen: Anytime-Valid, Metric-Agnostic Decision Certificates for Generative-Model Comparison**, targeting a possible CVPR 2027 paper.

Read `CERTGEN_PROJECT_MASTER_CONTEXT.md` completely before coding.

## Mission

Build V1 basics only. Create a clean, CPU-testable repository foundation for CertGen. Do not run real experiments. Do not fabricate results. Do not claim any real empirical finding. All V1 outputs must be smoke/non-evidence.

## What CertGen is

CertGen is a metric-agnostic decision/certificate layer for generative-model comparison. It asks when one generative model is certifiably better than another under a chosen metric, how many samples were needed to decide, and whether the verdict remains valid under optional stopping.

It is not a new metric, not a “FID is bad” paper, not a leaderboard replacement, and not a new statistical theory paper.

## Hard constraints

- zero cost;
- no paid APIs;
- no paid GPUs;
- no paid annotation;
- no large downloads in tests;
- no GPU work in tests;
- no mandatory heavy dependencies;
- all mock/smoke/planned artifacts are non-evidence;
- no fake numbers;
- no fabricated citations;
- no real audit claims.

## Build tasks

### 1. Repository scaffold

Create package and docs:

```text
certgen/
  cli/
  core/
  schemas/
  metrics/
  certs/
  gates/
  reporting/
  pilots/
  features/
configs/
docs/
tests/
registry/
data/results/  # generated only if needed
```

Create `pyproject.toml`, `README.md`, and `configs/certgen_v1_smoke.yaml`.

### 2. Schemas and evidence statuses

Implement dataclass schemas for:

- DatasetRecord;
- ModelRecord;
- FeatureManifest;
- MetricRecord;
- ComparisonRecord;
- DecisionCertificate;
- CandidateBenchmark;
- CandidateModelPair;
- AuditClaimRecord.

Every artifact must carry an evidence status. V1 may only generate non-evidence artifacts.

### 3. Claim gates

Implement claim gates that block forbidden result language in smoke/non-evidence outputs. Forbidden phrases include:

- `we find that`
- `we show that`
- `certified result`
- `paper evidence`
- `real evidence`
- `model A beats model B`
- `published wins are undecided`
- `ranking changes`
- `compute saving`
- `empirical result`

### 4. Feature foundation

Implement local `.npz` feature-array save/load and manifest validation. Add feature-extraction CLI stubs for Inception, CLIP, and DINOv2 with `--dry-run`, optional dependencies only, and no real output by default.

### 5. Metrics foundation

Implement CPU-safe array metrics:

- MMD with polynomial kernel and optional RBF;
- KID wrapper over polynomial MMD;
- CMMD wrapper over MMD on CLIP-like features;
- FID descriptive point estimate;
- FD-DINOv2 descriptive wrapper.

FID must be `descriptive_only` in V1 and must not support clean CS.

### 6. Certificate core

Implement a conservative confidence-sequence scaffold over a stream of delta contributions. It may be Hoeffding-style or empirical-Bernstein-style, but must honestly label the method.

Decision rule:

- CS upper < 0 → `certified_a_better`
- CS lower > 0 → `certified_b_better`
- otherwise → `not_decided_at_budget`

In V1, even such toy statuses remain non-evidence smoke artifacts.

### 7. FID policy gate

Implement a gate that prevents FID from entering the clean certificate path. FID reports must be descriptive-only or experimental/non-evidence.

### 8. Pilot registry

Create registry templates for candidate benchmarks and model pairs. Do not invent reported scores. Missing values must stay missing. Add CLI to validate registry and generate a first-pilot TODO plan.

### 9. Reporting and docs

Create:

- `docs/CERTGEN_V1_README.md`
- `docs/CLAIMS_POLICY.md`
- `docs/FID_POLICY.md`
- `docs/EVIDENCE_STATUS_POLICY.md`
- `docs/RUNBOOK_V1.md`
- `docs/NO_RESULTS_YET.md`
- `docs/REPRODUCIBILITY_CAPSULE_V1.md`
- `docs/COMMAND_INDEX_V1.md`
- `docs/RELATED_WORK_TODO.md`
- `docs/REVIEWER_ATTACKS_V1.md`
- `docs/FIRST_PILOT_CHECKLIST.md`

`NO_RESULTS_YET.md` must explicitly state that CertGen currently has no real empirical results, no audit number, no decidedness fraction, no ranking changes, and no paper evidence.

### 10. Final V1 audit

Implement:

```bash
python -m certgen.cli.v1_audit --out docs/V1_FINAL_AUDIT.md --json-out data/results/v1_final_audit.json
```

Audit checks:

- imports;
- config validation;
- schema serialization;
- evidence gate;
- claim gate;
- FID policy gate;
- smoke metrics;
- toy certificate;
- report claim safety;
- no real evidence artifacts;
- registry templates;
- no-results documentation.

## Required commands

At minimum, support:

```bash
python -m certgen.cli.validate_config --config configs/certgen_v1_smoke.yaml
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics --make-certificate
python -m certgen.cli.validate_registry --benchmarks registry/candidate_benchmarks_template.csv --pairs registry/candidate_model_pairs_template.csv
python -m certgen.cli.plan_first_pilot --pairs registry/candidate_model_pairs_template.csv --out docs/FIRST_PILOT_PLAN.md
python -m certgen.cli.v1_audit --out docs/V1_FINAL_AUDIT.md --json-out data/results/v1_final_audit.json
python -m pytest -q
```

## Tests

Add tests for:

- imports;
- config validation;
- schema serialization/hash determinism;
- evidence status enforcement;
- claim gate blocking forbidden language;
- FID policy blocking clean-CS FID;
- MMD/KID/CMMD toy behavior;
- FID descriptive status;
- smoke certificate behavior;
- report claim safety;
- registry templates.

## Final response format

When finished, report:

1. files created/modified;
2. commands implemented;
3. tests run and exact result;
4. V1 audit result;
5. limitations;
6. next step for V2.

Do not claim paper readiness. Do not claim real empirical results.
