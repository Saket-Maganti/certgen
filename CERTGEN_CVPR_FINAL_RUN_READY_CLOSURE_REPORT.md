# CertGen CVPR Final Run-Ready Closure Report

Final status: `CVPR_RUN_READY_BLOCKED_ONLY_BY_REFERENCE_INPUT`.

## Required closure answers

1. The minimum pilot can be prepared from the current registries; its selection-aware preflight package was built and validated locally.
2. Selected models: `google_ddpm_cifar10_candidate` and `frank_ddpm_ema_cifar10_candidate`.
3. Selected extractors: `inception` and `clip`.
4. `frank_cfm_cifar10_candidate` and `dinov2` remain registered but excluded; selecting either unresolved lane fails closed.
5. Inception offline loading is verified with an exact-enum, SHA-bound local-state-dict fixture. A real Kaggle preflight is still required.
6. The CLIP estimand is explicit: the 768-dimensional projected image embedding from `CLIPModel.get_image_features`, followed by L2 normalization.
7. Generation, import, feature preparation, workers, merge, and cache sidecars share the canonical `relative_image_path` schema.
8. The 1k feature package defaults to embedded canonical relative images; every path is opened, decoded, dimension-checked, and hash-checked before GPU allocation.
9. The real builders pass the builder-faithful synthetic chain through deterministic ZIPs, secure imports, merge, cache-v2, family, certificate, and partial ranking.
10. Prospective cross-feature, ranking-stability, point-versus-certified, compute-accounting, and qualitative-gallery contracts exist and pass fixture tests.
11. Profile-bound preregistration freeze works, propagates a study hash, and feeds the canonical six-hypothesis minimal family.
12. No known local run-continuity defect remains after final local-safe verification.
13. Exact blocker: `BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE`.
14. Exact next command:

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```

15. No further pre-run patch is justified absent an observed real-execution failure covered by the stop-building rule.

## Verification seal

- Tests: `258 passed, 4 deselected`; integration audits: `4 passed`; focused statistical/artifact/runtime/closure lane: `66 passed`; new closure lane: `8 passed`.
- Compilation, ten critical imports, Ruff, scoped mypy (34 source files), notebook static analysis (5/5), byte-identical notebook regeneration (5/5), registry/artifact/CVPR/forensic/V9 audits, paper/release/privacy firewalls, paper compilation, and `git diff --check` pass.
- Full mypy remains exactly the historical debt baseline: `111 errors in 34 files` while checking 286 source files; no new critical-scope errors exist.
- The portable preseal archive verified 750 members, 10 portable tests, five notebook static checks, and the 21-stage synthetic runtime without `.git`.
- No CIFAR archive, checkpoint, Kaggle job, CUDA execution, real generation, real feature extraction, metric result, certificate, or paper result was created. Every fixture remains `synthetic_validation_only`, `not_model_evidence`, and `claim_allowed=false`.

No further broad or targeted pre-run infrastructure development is justified. The repository is ready for official CIFAR reference validation, materialization, study freeze, and the first real Kaggle preflight.
