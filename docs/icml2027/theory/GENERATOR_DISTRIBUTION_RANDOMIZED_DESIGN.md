# Prospective generator-distribution randomized design

Status: `PLANNING_ONLY / NOT_CONFIRMATORY_ELIGIBLE`

Contract ID: `icml2027_generator_randomized_inference_v1`
This document does not modify the frozen legacy 1k pilot or CIFAR 10k v2 study. `claim_allowed=false`.

## Target and randomization law

For generator (g\in\{A,B\}), predeclare an IID seed sequence (S^g_1,S^g_2,\ldots\sim P_S), independent across generators and independent of the IID reference draws (R_1,R_2,\ldots\sim P_R). The law (P_S), domain separation, seed-to-framework conversion, generator version, sampler, scheduler, precision, conditioning, and output postprocessing must be frozen before any generated output is observed. The model output map is the deterministic measurable map (X^g_t=G_g(S^g_t)) after those choices are fixed.

The population target for a frozen bounded kernel (k) and feature map (\phi) is

\[
\Delta_{A,B}=\operatorname{MMD}^2(P_{\phi(X^A)},P_{\phi(R)})-
\operatorname{MMD}^2(P_{\phi(X^B)},P_{\phi(R)}).
\]

The implemented paired contribution map remains

\[
Z_t=k(A_{2t-1},A_{2t})-k(B_{2t-1},B_{2t})
-k(A_{2t-1},R_{2t})-k(A_{2t},R_{2t-1})
+k(B_{2t-1},R_{2t})+k(B_{2t},R_{2t-1}),
\]

with (Z_t\in[-3,3]) for the frozen bounded RBF kernel and (E[Z_t]=\Delta_{A,B}) under the stated IID law.

## Filtration and optional stopping

Let (\mathcal F_t) contain the authenticated study identity and all seeds, reference draws, generator outputs, features, and contributions revealed through unit (t). The required sequential assumption is (E[Z_t\mid\mathcal F_{t-1}]=\Delta_{A,B}), together with the bounded support. Under that assumption, the existing summable-error union-Hoeffding confidence sequence covers (\Delta_{A,B}) simultaneously at all integer times; first exclusion of zero therefore permits optional stopping at the predeclared rule. Bonferroni allocation applies across the prospectively frozen comparison family.

## Precommitment and separation from existing studies

Before execution, a new study version must freeze the seed law, independence construction, generator/checkpoint and local-asset identity, reference law, feature spaces, kernel/gamma, pairing, family, alpha allocation, maximum budget, stopping rule, missing-data behavior, and replay contract. A finite fixed seed manifest is a realized randomized design only when it was generated from this law before outcomes and its generation procedure is authenticated. Conditional replay of an arbitrary fixed manifest does not by itself identify the generator-distribution population target.

## Open proof and implementation obligations

- Prove the seed-to-output map and generator execution satisfy the declared independence construction in the actual multi-worker runtime.
- Bind the randomization-law version and its authenticated generation transcript to worker specs and returned payloads.
- Prove the paired stream has the required constant conditional mean under any reference reuse and multipart/resume behavior actually used.
- Define how generator failures or rejected samples enter the target without outcome-dependent resampling.
- Complete an independent theorem-to-code review before any confirmatory promotion.

Until those obligations are discharged, status remains `PLANNING_ONLY / NOT_CONFIRMATORY_ELIGIBLE`; no population claim may be inferred from the legacy 1k or frozen CIFAR 10k manifests. `synthetic_validation_only=true`, `not_real_generator_evidence=true`, `not_empirical_paper_evidence=true`, `claim_allowed=false`.
