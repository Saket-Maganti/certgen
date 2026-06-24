# V2 Confidence Sequence Core

`NO_REAL_EVIDENCE`

Implemented:

- Conservative time-uniform Hoeffding union-bound confidence sequences.
- Conservative practical empirical-Bernstein-style confidence sequences.

Assumptions:

- Stream values are finite and bounded.
- Bounds are declared directly or produced by explicit clipping with metadata.

This differs from fixed-n bootstrap/error bars because intervals are designed for continuous monitoring over time. The empirical-Bernstein variant is practical and conservative, not a new theoretical claim.

FID is excluded from rigorous clean-core CS because FID is a biased nonlinear function of empirical means and covariances.
