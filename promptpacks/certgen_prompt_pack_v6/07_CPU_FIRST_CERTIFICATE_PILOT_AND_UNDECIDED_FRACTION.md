# 07 — CPU First Certificate Pilot and Undecided Fraction

Implement/execute `CERTGEN_R1E_CPU_FIRST_CERTIFICATE_PILOT`.

Goal:

> Run the first real clean-core certificate pilot on cached features and compute the pilot-only first-benchmark undecided fraction.

This is the first step that may produce real empirical pilot numbers, but they must remain `pilot_only`, `single_benchmark_only`, and `not_paper_claim`.

## Prerequisites

- R1D reports `READY_FOR_CPU_CERTIFICATE_PILOT`.
- Feature caches validated.
- Metric reproduction or sanity gate passed.
- No FID certificate claim.
- Bounded RBF-MMD / bounded CMMD available.
- Polynomial KID not certified by default.

## Candidate comparisons

Run clean-core certificates for:

1. null calibration: reference split vs reference split;
2. obvious-gap sanity: reference vs corruption/noise;
3. google DDPM vs Frank CFM;
4. google DDPM vs Frank DDPM EMA;
5. preprocessing sensitivity pair if available.

## Metrics

Certified:

- bounded RBF-MMD on Inception or normalized features;
- bounded CMMD / RBF-MMD on CLIP features.

Descriptive only:

- FID;
- FD-DINOv2;
- polynomial KID.

## Outputs

- `data/results/r1e_clean_core_certificates/*.json`
- `docs/R1E_FIRST_CERTIFICATE_PILOT_REPORT.md`
- `data/results/r1e_undecided_fraction.json`
- `docs/R1E_UNDECIDED_FRACTION_PILOT_ONLY.md`
- certificate cards for each comparison.

Every output must include:

- `evidence_status=pilot_only`
- `claim_allowed=false`
- `not_paper_claim=true`
- `single_benchmark_only=true`

## Required numbers

Compute:

- number of valid pilot comparisons;
- number decided;
- number undecided;
- undecided fraction;
- samples-to-decision for decided pairs;
- null calibration decision status;
- obvious-gap sanity decision status.

## Go/no-go interpretation

- If null calibration decides: severe blocker.
- If obvious-gap sanity does not decide: certificate too weak or pipeline issue.
- If all real pairs decide trivially: audit headline may be weak.
- If many real pairs are undecided: strong reason to scale.

## Audit

Add:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.r1e_first_pilot_audit \
  --out docs/R1E_FIRST_PILOT_AUDIT.md \
  --json-out data/results/r1e_first_pilot_audit.json
```

Checks:

- all outputs pilot_only;
- no `claim_allowed=true`;
- null calibration included;
- obvious-gap sanity included;
- no FID certificate;
- undecided fraction labeled not paper claim.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
```

Final response:

- tests passed;
- audit passed;
- undecided fraction;
- null calibration status;
- obvious-gap status;
- next decision: scale / fix / stop.
