# CertGen final closure audit

Final engineering status: `ICML2027_FINAL_CLOSURE_COMPLETE_LEGACY_AND_ICML_GPU_PATH_READY`.

This status means the unchanged legacy 1k GPU path is ready and the new 10k/DINO execution transport is closed. It does not mean the project is empirically ICML-ready. Real GPU evidence is absent, and statistical power is the main scientific risk.

## Acceptance

1. PASS — Legacy 1k path unchanged.
2. PASS — Fresh dependency lifecycle implemented.
3. PASS — Restart identity-bound.
4. PASS — READY notebooks self-manage dependency state.
5. PASS — Generation transports scientific payload.
6. PASS — Features transport scientific payload.
7. PASS — Multipart/copy-forward validated.
8. PASS — Missing/corrupt parts fail.
9. PASS — Worker specs bind study/config.
10. PASS — Partitions exact.
11. PASS — Sample IDs separate from RNG seeds.
12. PASS — Seed manifest frozen/regenerable.
13. PASS — Workers consume exact seeds.
14. PASS — Feature identity exact.
15. PASS — Probability space matches finite-manifest implementation.
16. PASS — Invariance controls excluded.
17. PASS — True-alternative power recomputed.
18. PASS — Union-Hoeffding remains canonical.
19. PASS — No unverified method promoted.
20. PASS — Generation-to-feature fixture passes.
21. PASS — Identity mutations fail.
22. PASS — 10k memmaps feasible.
23. PASS — Launchboard vocabulary truthful.
24. PASS — DINO robustness-only.
25. PASS — Cross-family external-source blocked.
26. PASS — Full tests pass.
27. PASS — Security/provenance/replay pass.
28. PASS — Ruff passes.
29. PASS — Changed-code mypy passes.
30. PASS — Historical mypy debt not increased.
31. PASS — Release verifies.
32. PASS — claim_allowed=false.
33. PASS — Git push parity verifies.

## Final verification ledger phases

- `final_default_pytest`: `PASS`
- `final_full_marker_pytest`: `PASS`
- `final_integration_wrappers`: `PASS`
- `final_ruff`: `PASS`
- `final_changed_mypy`: `PASS`
- `final_full_mypy`: `EXPECTED_BOUNDARY`
- `final_security_release`: `PASS`
- `final_diff_check`: `PASS`

- Seed manifest: `875ce5637b2596c5e12cbc3ffc0ee76b19c12282290a4a59b75e5d9daa4853d0`
- Execution contract: `7f0a2899aa9d320076562fb4dda530dada25a9c09bde4da3541ca395ac52d6d2`
- Full CPU rehearsal: `86721319fb1ac4c56567a3ac593f5cb9634ef5e43f635dec4c0c0949d4094d7d`
- Current local HEAD during report generation: `3506826ceb7fda0b46b514f43f17e38b6e62aac3`
- `real_gpu_evidence_exists=false`; `empirical_paper_evidence_ready=false`; `claim_allowed=false`.
