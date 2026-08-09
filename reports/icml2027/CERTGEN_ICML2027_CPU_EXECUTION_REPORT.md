# CertGen ICML 2027 — CPU Execution Report

All results in this report are engineering or synthetic-validation evidence only. They are not real-generator or empirical paper evidence. `claim_allowed=false`.

All locally feasible tiers completed; no CPU runs remain.

| Tier | Synthetic records | Scenarios | Measured wall time | Status |
|---|---:|---:|---:|---|
| quick | 672 | 28 | 4.736 s | PASS |
| medium | 14,336 | 28 | 4.904 s | PASS |
| overnight | 112,000 | 28 | 27.790 s | PASS |

The overnight lane also completed 5,000-replicate optional-stopping and 5,000-replicate family-multiplicity studies, 2,000 representation replicates (6,000 rows), 540 baseline-power executions, 26 finite-sample diagnostics, replay, fixtures, gates, notebook checks, and all 13 baselines. Bulk Monte Carlo artifacts remain intentionally untracked and are reproducible from frozen configs.
