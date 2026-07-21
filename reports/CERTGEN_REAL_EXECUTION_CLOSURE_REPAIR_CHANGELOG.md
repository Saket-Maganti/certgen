# CertGen Real-Execution Closure Repair Changelog

| Defect | Repair | Verification |
|---|---|---|
| Model/extractor preflight evidence was too weak | Builders require matching status/config/run identity, successful load/smoke, calibration, preprocessing, and imported asset hashes | closure and builder-faithful tests |
| GPU launch could oversubscribe devices | Deterministic one-active-worker-per-GPU queues | queue failure/timeout/resume tests |
| Frozen generation semantics were not family-specific | Text/class adapters derive batches from frozen prompt/label/seed inputs; requested/applied differences are recorded | adapter regression tests |
| CFM/unknown adapters were optimistic | Explicit fail-closed routing before packaging | unsupported-adapter tests |
| Asset layout and network modes were conflated | Canonical snapshots plus independent dependency/asset policy | asset/network tests |
| Feature preparation/merge was incomplete | Role manifests, non-mixing shards, cache-v2 merge/validation/registration | 27-stage synthetic rehearsal |
| Family selection used inconsistent status fields | Frozen study and actual registry fields drive full cartesian family | family tests |
| Notebook/import schema had multiple sources | Shared output validator is invoked by importer | schema/import tests |
| Valid checkpoint extensions were blocked | `.pt`, `.pth`, `.ckpt`, `.model` permitted; traversal and transient `.cache` content rejected/excluded | output/final-ZIP tests |
| Root and nested status files were conflated | Root identity/config/status are canonical; nested worker status is allowed | output schema tests |
| Canonical run ID was lost on import | Safe run ID is preserved from root `run_identity.json` | import-repair test |
| Resume markers trusted unsafe output paths/hashes | Relative path and SHA-256 validation precede byte verification | resume security tests |
| Historical non-retained artifacts failed the live audit | Explicit lifecycle states warn; fresh missing files remain errors | artifact-registry tests/audit |
| Local reference candidate was reported as absent | Readiness detects the root candidate and emits validation—not materialization—as the one next action | readiness/Phase‑1/V9/CVPR audits |
| Closure ledger/archive evidence was stale | Portable CPU-only runner, updated reports, clean archive rebuild | full suite and archive manifest |

No theory, metric result, model label, benchmark result, or paper evidence was created.
