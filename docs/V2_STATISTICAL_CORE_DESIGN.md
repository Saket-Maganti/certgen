# V2 Statistical Core Design

`NO_REAL_EVIDENCE`

CertGen V2 targets `Delta_AB = d(A, R) - d(B, R)`, where lower distance is better. Negative stream means indicate A is closer to the reference under a clean metric; positive stream means indicate B is closer.

Clean-core certifiable metrics are MMD/KID/CMMD-style metrics with contribution streams. Descriptive metrics are FID and FD-DINOv2 unless a later proof-backed implementation changes that policy.

Data model:

- Feature arrays for model A, model B, and reference samples.
- Two-dimensional finite float arrays.
- Deterministic seeded pairing for stream construction.
- Optional streaming mode over bounded/clipped contribution units.

Contribution streams:

- Each unit `h_i` estimates a component of `MMD^2(A, R) - MMD^2(B, R)`.
- Negative means A closer; positive means B closer.
- Clipping must record bounds and clipping fractions.

Confidence sequences target a time-uniform interval for `E[h_i]`. Stop when the interval excludes zero; otherwise report `not_decided_at_budget`.

Risks include dependence between terms, feature reuse, kernel sensitivity, boundedness/clipping tradeoffs, and FID nonlinearity.

V2 certificates remain non-evidence unless real feature provenance and registry gates pass in a later version.
