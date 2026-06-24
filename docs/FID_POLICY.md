# FID Policy

FID is nonlinear in empirical means and covariances, and finite-sample FID is biased. A naive confidence sequence over a sequence of FID point estimates does not make FID an optional-stopping-safe mean estimator.

V1 allows FID only as:

- FID descriptive estimate
- FID point estimate
- FID block-level exploratory analysis
- KID/CMMD certificate with FID shown descriptively

V1 forbids:

- FID-certified winner
- anytime-valid FID result
- rigorous FID certificate
- FID proves A beats B

The future V2 path must either prove a watertight FID treatment, keep FID descriptive, or use FID only beside a clean-core KID/MMD/CMMD certificate.
