# CertGen ICML 2027 deep-repair baseline

- Starting commit: `463e52753646e7d2b0792e90b9d92e4956b634f2`
- Remote `origin/main`: `463e52753646e7d2b0792e90b9d92e4956b634f2`
- Branch: `main`
- Initial status: three pre-existing untracked prompt-pack Markdown files; preserved
- Python: `3.11.9 (v3.11.9:de54cf5be3, Apr  2 2024, 07:12:50) [Clang 13.0.0 (clang-1300.0.29.30)]`
- Platform: `macOS-26.5.2-arm64-arm-64bit` / `arm64`
- Normal pytest: `326 passed, 4 deselected`
- Full marker-enabled pytest: `330 passed`
- Explicit integration wrappers: `4 passed, 326 deselected`
- Trusted-bootstrap/security subset: `18 passed`
- Changed-code mypy: pass across 46 source files (includes the ledger runner)
- Historical repository mypy debt: `99 errors in 33 files` (371 files checked after adding the ledger runner)
- Ruff: pass
- Legacy study SHA-256: `346f0bea70d94803bd9da2793153496a6b0c1fe839174e8d2049773f5bfcc5ae`
- Legacy semantic study hash: `b6882b9e1be0b9f12868c47be44c0f41a522ed45c7a4529ceabd08f38cc991aa`
- Reference draw-plan SHA-256: `27bc56310998dd14fbf06fd096c432f1c21fe2389466a52383df8265468bff6f`
- Diagnostic package SHA-256: `d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d`
- Preflight package SHA-256: `d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f`

## Frozen ICML study contracts

- `icml2027_synthetic_validity_v1`: `e28e56714e6e4bb934a74932f351a00baef0269ad46cc918a8f5ed20b4b9bc12` (FROZEN_SYNTHETIC)
- `icml2027_cifar_confirmatory_10k_v1`: `6b1516b0f78681df1e966a29797b84110e110f46b834f65f623a43f09a9d2005` (FROZEN_WAITING_GPU)
- `icml2027_multi_model_synthetic_v1`: `981959ef501fc052ab89ddf7618310a346badcb46c08185a7ac042fad3d45f2e` (FROZEN_SYNTHETIC)
- `icml2027_representation_robustness_v1`: `10efe516ee20571e67ba0366b0bbbe2b291ab0bb85a241b966ec7973517b24dc` (FROZEN_SYNTHETIC)
- `icml2027_multibench_planning_v1`: `8ca4cf038b5bf0c1f4b37f76d50fd9e4c43872980109ba7f3e1c4caab9533902` (FROZEN_PLANNING)
- `icml2027_adaptive_ranking_v1`: `3623abc79b707c6e806c57fc23b47be7b08e7ca38a1a0df8bdb6ba3f7277dae9` (FROZEN_EXPLORATORY_SYNTHETIC)
- `icml2027_equivalence_v1`: `9618b9a5a49fa6c6525524cc857814d1c46f3bf58b891caa9eeddc95356a8647` (FROZEN_EXPLORATORY_SYNTHETIC)

Compile/import, live tests, integration wrappers, notebook regeneration checks, authenticated bundle validation, provenance, replay, privacy, secret, restricted-asset, release, Ruff, mypy, and diff checks were reproduced from the live checkout. `claim_allowed=false`.
