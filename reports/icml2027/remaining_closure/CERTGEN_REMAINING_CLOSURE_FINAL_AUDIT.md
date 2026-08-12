# CertGen ICML 2027 remaining-closure final audit

        Final status: **`CERTGEN_ICML2027_REMAINING_CLOSURE_COMPLETE_POWER_RESEARCH_REMAINS`**.

        The execution-path defects are closed and CPU science is complete for the mandatory/reused lanes. Engineering readiness is separate from launch readiness: 10k and DINO still require external authenticated assets; corrected statistical power remains RED; no real GPU evidence or paper evidence exists.

        ## Acceptance matrix

        1. PASS — legacy 1k identities match the starting baseline
2. PASS — no hidden/manual expected-input identity
3. PASS — exact input authentication remains fail-closed
4. PASS — canonical 10k generation worker builder
5. PASS — canonical 10k feature worker builder
6. PASS — canonical DINO and released-sample builders
7. PASS — authenticated local checkpoint loading
8. PASS — confirmatory worker does not fetch weights remotely
9. PASS — actual runtime provenance is expectation-checked
10. PASS — payload sidecars are the validated actual sidecars
11. PASS — DINO local model+processor and robustness gate
12. PASS — aggregate feature coverage rejects gaps/extras
13. PASS — deterministic generation fixture rehearsal
14. PASS — deterministic feature fixture rehearsal
15. PASS — offline asset fixture rehearsal
16. PASS — generator-distribution scope documented
17. PASS — no unsupported fixed-manifest population claim
18. PASS — corrected power and Wilson intervals computed
19. PASS — union-Hoeffding remains canonical
20. PASS — no unverified sharper method promoted
21. NOT APPLICABLE — no sharper candidate is eligible
22. PASS — resolution/effect map exists
23. PASS — variance/kernel studies are exploratory/prospective
24. PASS — hard multi-model study: 168 rows, FWER 0.0
25. PASS — CertGen-Active remains exploratory
26. PASS — 10k engineering/asset/statistical/power decisions separated
27. PASS — DINO decision explicit
28. PASS — launchboard uses truthful allowed statuses
29. PASS — final marker-inclusive suite count 386 plus historical wrappers
30. PASS — security/provenance/replay checks are ledgered
31. PASS — Ruff/changed-scope mypy; full mypy debt reduced from 91 to 89 errors
32. PASS — release/privacy/secrets/restricted-asset verification passed
33. PASS — claim_allowed=false throughout
34. PENDING COMMIT STEP — push parity is verified only after commit/push

        ## CPU work

        Completed now: corrected power/effect map, 600 variance-reduction replicates, 1,250 kernel/gamma runs, 168 hard multi-model rows through M=100, 28 adaptive-policy rows over seven policies, 12 high-dimensional C2ST rows, corrected bootstrap/asset/provenance multipart fixtures, and full verification. Reused: production quick/bounded-stress/null-100, boundary/fixed/permutation/bootstrap baselines, 10k×768/2048 feasibility, and prior overnight synthetic artifacts.

        No mandatory CPU run remains. Further power work is method development, not an unfinished executable job: complete a theorem-to-code map, create a new prospective config, then rerun the production stream benchmark. Do not tune or change frozen v2. Real 10k/DINO work is external/GPU-only and follows the launchboard/runbooks.

        `real_gpu_evidence_exists=false`; `paper_evidence_ready=false`; `claim_allowed=false`.
