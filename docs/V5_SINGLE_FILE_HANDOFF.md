# CertGen V5 Single-File Handoff

`NO_REAL_EVIDENCE`

Current project status:

CertGen is CVPR-ready-except-runs. The codebase, paper scaffold, supplement scaffold, result contracts, claim gates, reproducibility capsule, reviewer defenses, command bundles, and final audit exist. It is not submission-ready because no real claim-eligible empirical audit has been executed.

What V1-V5 built:

- V1: repository scaffold, smoke artifacts, basic claim gates, and reproducibility docs.
- V2: clean-core metric streams, confidence-sequence scaffolds, certificate API, feature-cache contracts, and FID descriptive policy.
- V3: provenance validation, real feature-cache validation, metric reproduction audit, first-pilot orchestration, replay, registry availability, and optional-stopping lab.
- V4: real-run planner, notebook generator, preprocessing locks, batch certificates, decidedness/ranking reports, first-real-pilot controller, literature tracing, paper artifact scaffolds, reviewer attacks, capsule, release scan, and V4 audit.
- V5: paper identity, claim contract, related-work board, preregistration lock, result contracts, main paper scaffold, supplement/proof scaffold, V5 release capsule, command bundles, result-injection protocol, reviewer simulator, CVPR readiness scorecard, kill list, stop condition, and final V5 audit.

Evidence boundary:

All V5 artifacts are `template_only`, `dry_run_only`, or `pilot_candidate` unless a later real run passes provenance, feature-cache, metric reproduction, certificate, result-injection, claim-trace, release, and final-audit gates. Pre-run outputs keep `claim_allowed=false`.

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m certgen.audit.v5_audit --out docs/V5_FINAL_AUDIT.md --json-out data/results/v5_final_audit.json
```

Exact next real execution steps:

1. Populate one real provenance ledger.
2. Validate or materialize real feature caches.
3. Reproduce one reported metric point estimate.
4. Run the first real clean-core pilot in non-claim mode.
5. Inspect the first-benchmark undecided fraction.
6. Decide whether to scale only after seeing the non-claim pilot.

Current limitations:

- no real benchmark audit;
- no claim-eligible empirical evidence;
- no final verified related-work citations;
- no measured decidedness endpoint;
- no paper-ready result tables or figures;
- FID/FD remains descriptive only.

What not to claim:

- no numeric decidedness endpoint;
- no benchmark result;
- no ranking-change conclusion;
- no savings number;
- no rigorous FID certificate;
- no statement that prior papers are wrong.

What would justify V6:

Only a concrete real-run failure: provenance schema mismatch, feature-cache schema mismatch, metric reproduction failure, certificate runtime/scale issue, result-injection contract mismatch, proof gap, paper-build failure, or release-safety failure.

Final verdict:

CertGen is now CVPR-ready-except-runs: the codebase, paper scaffold, result contracts, claim gates, reproducibility capsule, and reviewer defenses are prepared. It is not CVPR-submission-ready because no real claim-eligible empirical audit has been executed. The next step is real execution: populate one provenance ledger, validate/materialize real feature caches, reproduce one metric point estimate, run the first real clean-core pilot in non-claim mode, and only then evaluate the first-benchmark undecided fraction.
