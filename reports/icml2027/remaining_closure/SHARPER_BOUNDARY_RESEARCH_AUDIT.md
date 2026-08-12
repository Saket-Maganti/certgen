# Sharper boundary research audit

Canonical result: union-Hoeffding remains `VERIFIED_CONFIRMATORY_ELIGIBLE` and frozen. Best verified implemented sharper result: **`NONE_IMPLEMENTED_OR_CONFIRMATORY_ELIGIBLE`**. No method was promoted.

| Candidate | Primary theorem | Status | CertGen blocker |
|---|---|---|---|
| Predictable plug-in empirical Bernstein | Waudby-Smith & Ramdas, JRSS B 2024, Theorem 2 / equations 13–15 | `NOT_IMPLEMENTED` | Exact contribution transform, predictable variance, two-sided and familywise alpha mapping not completed |
| Betting CS/e-process inversion | Waudby-Smith & Ramdas, JRSS B 2024, Theorem 1 and Section 4 | `NOT_IMPLEMENTED` | No CertGen e-process, numerical inversion, or proof-to-code map |
| Adaptive stitched Bentkus | Kuchibhotla & Zheng, PMLR 139 (2021), Theorems 2–4 | `NOT_IMPLEMENTED` | Independence assumption not proved for paired shared-reference filtration; q inversion absent |

Primary sources: <https://academic.oup.com/jrsssb/article/86/1/1/7043257> and <https://proceedings.mlr.press/v139/kuchibhotla21a.html>. The machine-readable registry records source statements, assumptions, time-uniform claims, alpha-mapping status, and eligibility. Because no sharper candidate is both implemented and theorem-mapped, no fair production-stream benchmark against such a candidate is claimed. Existing fixed-N, permutation, bootstrap, logistic C2ST, and union-Hoeffding baselines remain the truthful comparison set. `claim_allowed=false`.
