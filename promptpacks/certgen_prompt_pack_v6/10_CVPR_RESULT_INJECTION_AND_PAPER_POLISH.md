# 10 — CVPR Result Injection and Paper Polish from Real Outputs Only

Implement `CERTGEN_R4_CVPR_RESULT_INJECTION_FROM_REAL_OUTPUTS_ONLY`.

Goal:

> Once real pilot/full outputs exist, inject results into paper tables/figures only through claim gates and result contracts.

Do not fill paper with placeholders as if they were results.

## Prerequisites

At minimum:

- real feature caches validated;
- metric reproduction/sanity gates passed;
- certificate outputs generated;
- pilot/full evidence status clear;
- no FID certificate claim;
- result contracts pass.

## Tasks

### 1. Result eligibility checker

Before any table/figure/paper injection, check:

- source provenance;
- license status;
- sample manifest;
- feature cache validation;
- metric reproduction;
- certificate validity;
- multiplicity policy if leaderboard claims;
- evidence status.

Only eligible outputs can enter paper as evidence.

### 2. Paper table contracts

Create/validate tables:

- Decidedness audit table;
- Samples-to-decision table;
- Metric disagreement table;
- Null and sanity calibration table;
- Preprocessing sensitivity table;
- Runtime/resource table.

### 3. Figures

Create figure builders for:

- main audit figure: decided vs undecided comparisons;
- samples-to-decision curves;
- null calibration plot;
- optional stopping false-decision demonstration;
- ranking stability map.

### 4. Abstract/title update

Use result-dependent abstract only after real values exist.

Preferred title:

> Are Reported Generative-Model Wins Statistically Decided? An Anytime-Valid Audit

Alternative:

> How Many Samples Until You Know? Anytime-Valid Certificates for Generative-Model Comparison

### 5. Reviewer defense update

Only update author-response bank based on real results.

No fake numbers.

## Output

- `docs/R4_RESULT_ELIGIBILITY_REPORT.md`
- updated paper tables/figures if eligible
- `docs/R4_PAPER_INJECTION_AUDIT.md`
