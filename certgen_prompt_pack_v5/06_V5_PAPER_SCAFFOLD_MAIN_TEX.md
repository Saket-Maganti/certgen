# 06 — V5 CVPR Main Paper Scaffold

## Goal

Create a CVPR-style main paper scaffold that is ready for result injection but contains no fake claims.

## Add Files

Create a `paper/` directory if it does not exist:

- `paper/main.tex`
- `paper/sections/00_abstract.tex`
- `paper/sections/01_introduction.tex`
- `paper/sections/02_related_work.tex`
- `paper/sections/03_method.tex`
- `paper/sections/04_experimental_protocol.tex`
- `paper/sections/05_results_placeholder.tex`
- `paper/sections/06_limitations_ethics.tex`
- `paper/sections/07_conclusion.tex`
- `paper/tables/README.md`
- `paper/figures/README.md`
- `docs/paper/PAPER_BUILD_GUIDE.md`
- `certgen/audit/paper_scaffold_audit.py`
- `tests/test_v5_paper_scaffold.py`

## Abstract Rules

The abstract must be result-free. It may say:

- generative-model comparisons are often based on finite-sample metric estimates;
- optional stopping can invalidate naive repeated monitoring;
- CertGen provides a metric-agnostic decision-certificate framework;
- empirical audit results will be inserted only after real runs.

It must not say:

- any fraction of wins are undecided;
- CertGen changes specific rankings;
- any model beats another;
- any sample savings number;
- most papers are wrong.

Use placeholder line:

`[REAL AUDIT RESULT SENTENCE TBD AFTER CLAIM-ELIGIBLE RUNS]`

## Introduction Structure

The introduction should establish:

1. Generative model papers often compare finite-sample metrics.
2. Point estimates do not by themselves answer whether a win is statistically decided.
3. Repeated monitoring/peeking requires optional-stopping-safe inference.
4. CertGen is a decision layer, not a new metric.
5. The paper's empirical audit will quantify decidedness after real runs.

## Method Section

Include subsections:

- Problem setup.
- Metrics as black-box discrepancy functions.
- Clean-core MMD/KID/CMMD stream construction.
- Anytime-valid decision certificate.
- Stopping rule and verdict taxonomy.
- Multiple comparisons and dependence diagnostics.
- FID/FD policy and limitations.

## Experimental Protocol Section

Result-free but concrete:

- benchmarks to be selected by provenance gates;
- model pairs must have released samples or reproducible checkpoints;
- preprocessing locks;
- feature caches;
- metric reproduction gates;
- pilot and main audit plan.

## Results Section

Create a placeholder results section with table/figure references only. Each paragraph must include `TBD_REAL_RUN_REQUIRED` until result injection.

## Build

If LaTeX is unavailable, provide a structural validator instead of failing. The audit should accept either:

- successful LaTeX build; or
- structural validation pass with a documented missing-LaTeX warning.

## Tests

Test that:

- all section files exist;
- forbidden empirical claim phrases are absent;
- all result paragraphs have placeholders;
- paper includes limitations/FID policy;
- paper build guide exists.
