# Empirical-Bernstein confidence sequence candidate

- Status: `NOT_IMPLEMENTED` and not confirmatory-eligible.
- Primary source: [Howard et al., “Time-uniform, nonparametric, nonasymptotic confidence sequences”](https://arxiv.org/abs/1810.08240), Section 4.1 and its empirical-Bernstein corollary.
- Exact theorem candidate: the paper's Section 4.1 empirical-Bernstein confidence sequence, built from predictable squared deviations and a sub-exponential uniform boundary.
- Assumptions requiring verification: adapted observations, bounded/sub-exponential increment condition, predictable center, intrinsic-time definition, and mapping from a confidence sequence for a cumulative conditional mean to CertGen's prefix-average estimand.
- Time-uniform statement and alpha conversion: supplied by the cited theorem; the exact one/two-sided conversion and Bonferroni split have not been transcribed and independently checked in this repository.
- CertGen mapping status: incomplete. Low contribution variance makes the candidate promising, but no formula is promoted.
- Limitation: theorem-to-code verification and numerical edge-case tests remain research work.
