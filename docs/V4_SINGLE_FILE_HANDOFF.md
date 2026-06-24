# CertGen V4 Single-File Handoff

`NO_REAL_EVIDENCE`

Project status after V4:

CertGen is now CVPR-run-ready in infrastructure terms. V4 added real-run planning, notebook generation, preprocessing locks, batch certificate audits, decidedness/ranking scaffolds, first-real-pilot control, literature claim tracing, paper artifact templates, reviewer attacks, and release/capsule checks.

What V4 added:

- V4 state intake and destructive audit.
- Provenance-to-real-run planner.
- Kaggle/Colab/local feature notebook generator.
- Strict preprocessing lock validator.
- Metric reproduction gate reuse for V4 smoke configs.
- Batch clean-core certificates with multiplicity metadata.
- Dependence diagnostics and sensitivity-facing report surfaces.
- Decidedness and ranking-stability audit outputs.
- First-real-pilot controller with go/no-go labels.
- Reported-claim ingestion and claim trace schema.
- Paper figure/table/result-card scaffolds.
- CVPR paper scaffold, related-work board, and claim-language policy.
- Reviewer attack harness and author-response bank.
- Reproducibility capsule validator and release safety scan.
- V4 final audit and command index.

Tests and audit status:

- Run the test suite with `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q`.
- Run the final V4 audit with `python3 -m certgen.audit.v4_audit --out docs/V4_FINAL_AUDIT.md --json-out data/results/v4_final_audit.json`.
- The audit writes machine-readable status to `data/results/v4_final_audit.json`.

Evidence boundary:

All V4 generated artifacts are infrastructure, smoke, synthetic, planned, dry-run, or real-unverified scaffolds. They are not paper evidence. They must remain `claim_allowed=false` until real provenance, feature-cache, metric reproduction, certificate, claim-language, and release gates all pass.

Current blockers:

- no real benchmark audit yet;
- no verified released-sample/model-pair provenance ledger row yet;
- no validated real feature caches yet;
- no reproduced reported metric point estimate yet;
- no real decidedness fraction yet;
- no real ranking movement claim;
- FID/FD remains descriptive-only;
- paper claims remain blocked.

Commands:

- See `docs/COMMAND_INDEX_V4.md` for the exact V4 command surface.
- Most generated V4 reports live under `docs/`.
- Most generated V4 JSON/CSV outputs live under `data/results/v4/`.

Go/no-go number still needed:

The first real clean-core pilot must report the non-claim first-benchmark undecided fraction and samples-to-decision distribution. Until that number exists, the project cannot know whether the CVPR empirical story is strong, conditional, or not worth pushing.

Exact next V5 action:

populate one real provenance ledger with verified released sample/model-pair rows, materialize or validate real feature caches, reproduce one reported metric point estimate, and run the first real clean-core pilot in non-claim mode to measure the first-benchmark undecided fraction

Warning:

Do not build endless infrastructure after V4 unless a real run exposes a concrete missing gate. The project now needs one carefully bounded real pilot more than another scaffold layer.
