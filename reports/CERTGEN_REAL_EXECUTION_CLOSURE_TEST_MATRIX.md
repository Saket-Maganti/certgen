# CertGen Real-Execution Closure Test Matrix

| Lane | Coverage | Final result |
|---|---|---|
| Model/extractor adapters | frozen config mapping, local loading, smoke/calibration contracts, unsupported CFM | PASS (fixtures/static; real loads not run) |
| GPU queues | serialization, deterministic assignment, crash isolation, timeout/recovery | PASS |
| Assets/network | canonical snapshots, identity/content hashes, independent policies | PASS |
| Builders/packages | strict preflight evidence, generation/features packages, dry inspection | PASS (fixtures) |
| Output/import | shared schema, root identity/config/status, extensions, integrity/security, canonical run ID | PASS |
| Feature merge/cache-v2 | identity, dedupe, sort, atomic output, validation/registration | PASS (synthetic) |
| Family | actual registry fields, frozen-study selection, cartesian hypotheses | PASS |
| Resume/final ZIP | safe relative outputs, SHA verification, quarantine, reuse/rebuild/restart/force-new | PASS |
| Builder-faithful rehearsal | 27 stages, 3 cache groups, 3 family certificates, partial ranking | PASS; synthetic non-evidence |
| Notebooks | five canonical notebooks plus Phase‑1 set | deterministic/static PASS; real Kaggle untested |
| Portable archive | clean extraction, package import, 12 tests, notebook audit, synthetic rehearsal | PASS; 834 members |
| Default suite | all local-safe non-recursive tests | `282 passed, 4 deselected` |
| Integration audit | recursive audit wrappers | `4 passed, 282 deselected` |
| Statistical lane | CS/MMD/certificate/reference-draw contracts | `31 passed` |
| Artifact lane | CVPR/schema/cache/runtime contracts | `25 passed` |
| Runtime closure lane | closure/readiness/post-cache/Phase‑1 contracts | `27 passed` |
| CVPR / forensic / V9 audits | end-state consistency and compatibility | `8/8`, `8/8`, `22/22` |
| Phase‑1 launch / CPU execution | package and CPU/GPU-boundary readiness | `11/11`, PASS |
| Critical mypy | 16 touched implementation sources | PASS; no issues |
| Full mypy | historical debt comparison | `111 errors in 34 files` across 310 checked files |
| Ruff / diff check | repository lint and whitespace integrity | PASS |

No lane used the internet, CUDA, real CIFAR contents, real checkpoints, real generation/features, or paper evidence.
