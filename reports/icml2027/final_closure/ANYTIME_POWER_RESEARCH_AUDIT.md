# Anytime power research audit

Union-Hoeffding remains the only confirmatory-eligible method. Its 5,000-unit terminal radius at alpha 0.05 is `0.276397319274`. The 100-replicate same-stream synthetic boundary benchmark passed; fixed-N Hoeffding remains comparator-only.

Empirical-Bernstein, stitching, conjugate-mixture, betting, and Bentkus candidates have primary-source research notes under `docs/icml2027/theory/boundaries/`. None has completed theorem-to-stream mapping, independent implementation verification, alpha conversion, and prospective freeze, so no sharper method is promoted.

Primary references include Howard et al. (2021), Waudby-Smith and Ramdas (2021/2023), and Kuchibhotla and Zheng (ICML 2021). Candidate performance must never be tuned using future real confirmatory outcomes.

`sharper_valid_boundary_available=false`; `claim_allowed=false`.
