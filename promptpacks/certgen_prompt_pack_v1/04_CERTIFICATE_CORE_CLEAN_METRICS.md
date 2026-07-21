# Prompt 04 — Certificate Core for Clean Metrics

## Objective

Implement the first non-evidence smoke version of the CertGen decision certificate for clean MMD/KID/CMMD-style metrics. The goal is to establish the contract, not to claim real results.

## Required context

Read:

- `CERTGEN_PROJECT_MASTER_CONTEXT.md`
- `00_GLOBAL_RULES_FOR_ALL_PROMPTS.md`
- Prompt 01–03 outputs

## Core comparison target

For two generated model sample sets A and B and a real/reference sample set R, CertGen compares:

```text
Delta_AB = d(A, R) - d(B, R)
```

Lower distance is better.

- If `Delta_AB < 0`, A is better.
- If `Delta_AB > 0`, B is better.
- If the confidence sequence contains 0 at budget, status is `not_decided_at_budget`.

## V1 certificate scope

V1 only needs a conservative smoke implementation that works on a stream of contribution values. It does not need to be the final paper-grade e-process. But the API must be honest and extensible.

Implement:

```python
certgen/certs/confidence_sequence.py
```

Functions/classes:

```python
class CSState:
    n: int
    mean: float
    lower: float
    upper: float
    alpha: float
    method: str
    optional_stopping_valid: bool

update_empirical_bernstein_cs(values, alpha, value_range=None) -> list[CSState]
```

If the exact empirical-Bernstein CS is not implemented yet, implement a conservative bounded Hoeffding-style CS and clearly label the method. Do not fake advanced theory.

Implement:

```python
certgen/certs/decision.py
```

Function:

```python
make_decision_certificate(
    comparison_record,
    delta_stream,
    alpha,
    max_samples,
    metric_record,
    evidence_status,
) -> DecisionCertificate
```

Stopping rule:

- if CS upper < 0: `certified_a_better`
- if CS lower > 0: `certified_b_better`
- otherwise at budget: `not_decided_at_budget`

But in V1 smoke mode, even if the toy stream excludes 0, the certificate must remain `non_evidence_smoke` and must not be called a paper result.

## Metric integration

Add a helper that can produce a toy delta stream from block estimates for KID/CMMD smoke arrays.

Do not claim the toy stream is a real metric estimator. It is for contract validation.

## Certificate JSON

A certificate JSON should include:

```json
{
  "certificate_id": "...",
  "comparison_id": "...",
  "metric_name": "kid_poly",
  "alpha": 0.05,
  "status": "not_decided_at_budget",
  "n_at_decision": null,
  "max_samples": 128,
  "lower": -0.12,
  "upper": 0.08,
  "point_estimate": -0.02,
  "optional_stopping_valid": true,
  "fid_rigor_status": null,
  "evidence_status": "non_evidence_smoke",
  "limitations": ["toy smoke stream", "not paper evidence"],
  "provenance": {...}
}
```

## CLI

Add:

```bash
python -m certgen.cli.make_smoke_artifacts \
  --config configs/certgen_v1_smoke.yaml \
  --out-dir data/smoke/v1 \
  --compute-metrics \
  --make-certificate
```

It should write:

```text
data/smoke/v1/certificates/smoke_kid_certificate.json
data/smoke/v1/reports/smoke_certificate_report.md
```

The report must pass the claim gate.

## Tests

Add tests that:

1. a negative delta stream eventually yields `certified_a_better` status in smoke mode;
2. a positive delta stream eventually yields `certified_b_better` status in smoke mode;
3. a near-zero/noisy stream yields `not_decided_at_budget`;
4. every certificate from smoke mode has `evidence_status=non_evidence_smoke`;
5. FID is rejected by the clean certificate path;
6. optional-stopping-valid flag is true only for supported methods;
7. report wording passes claim gate.

## Acceptance criteria

Run:

```bash
python -m pytest -q
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics --make-certificate
```

Then write `docs/V1_CERTIFICATE_CORE_REPORT.md` explaining exactly what is rigorous, what is smoke-only, and what remains for V2.
