# CertGen CVPR Statistical Core Audit

Status: `VERIFIED_CURRENT` for the local implementation; real-run assumptions remain `BLOCKED`.

The only claim-capable route is the prospectively fixed bounded-RBF comparison stream, union-Hoeffding confidence sequence, first-boundary crossing, and Bonferroni control over a frozen family. Tests and synthetic checks are not model evidence.

| Item | Verdict | Contract |
|---|---|---|
| Estimand | VERIFIED_CURRENT | Delta = MMD^2(A,R)-MMD^2(B,R) |
| Unit | VERIFIED_CURRENT | disjoint A pair, B pair, and shared-within-unit R pair |
| Contribution | VERIFIED_CURRENT | kAA-kBB-kAR1-kAR2+kBR1+kBR2 |
| Support | VERIFIED_CURRENT | each kernel term in [0,1], conservative contribution support [-3,3] |
| Direction | VERIFIED_CURRENT | negative means A closer; positive means B closer |
| Stopping | VERIFIED_CURRENT | first time the time-uniform interval excludes zero; ties/zero remain undecided |
| Time allocation | VERIFIED_CURRENT | alpha_t = 6 alpha/(pi^2 t^2), encoded through the union-Hoeffding radius |
| Resume | VERIFIED_CURRENT | identical stream prefix/configuration/reference plan only |
| Dependence | BLOCKED_REAL_RUN | IID/conditional-mean stream and prospectively fixed choices must be enforced by lineage |
| Multiplicity | BLOCKED_FREEZE | exact Cartesian family must be frozen before claim-bearing analysis |

Unsupported: betting-grid confidence intervals, empirical-Bernstein certificates, directional e-BH ranking, FID/FD certification, and polynomial-KID certification.
