# Full generation-to-feature rehearsal

Result: `PASS`. This is deterministic CPU fixture validation, not real generator evidence.

- Two fake models × 100 decoded PNGs; two generation shards/model; four multipart parts; validation `True`.
- Two fixture extractors; eight feature-cache parts; 400 validated finite rows; validation `True`.
- Copy-forward and local importer: PASS; four source-controlled worker subprocess fixtures: PASS.
- Production MMD certificate fixture: `UNRESOLVED` using `time_uniform_hoeffding_union_bound_v3`.
- Dependency compatible/install/restart/second-pass fixture: PASS.
- Identity mutation, missing/corrupt part, seed, order, extractor, preprocessing, and DINO-gate tests: PASS.

Fixture payload bytes remain ignored and uncommitted. `real_gpu_evidence_exists=false`; `claim_allowed=false`.
