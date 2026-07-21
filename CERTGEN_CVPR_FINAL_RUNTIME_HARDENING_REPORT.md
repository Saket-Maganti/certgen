# CertGen CVPR Final Runtime-Hardening Report

> Superseded for execution by `CERTGEN_CVPR_REAL_EXECUTION_CLOSURE_REPORT.md` and `CERTGEN_CVPR_RUN_READY_EXECUTION_HANDBOOK.md`. Retained only as a historical hardening record.

## 1. Executive verdict

Verdict: `CVPR_RUNTIME_HARDENED_BLOCKED_BY_REFERENCE_INPUT`.

All 11 known runtime leaks were confirmed in the live pre-edit implementation and repaired. New locally testable gaps were found in disk-failure proof, measured-preflight planner proof, failure injection coverage and combined lineage fingerprinting; they were repaired without adding a new generic V10/V11 layer. The five canonical notebooks are production-hardened at the source/static/fake-runtime level, but none has run on real Kaggle T4x2. Real reference validation, environment/model loading, generation, feature extraction, metric reproduction, certificates and CVPR evidence remain required. Exact blocker: `BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE`.

No further broad pre-execution upgrades are justified. The project must now execute the reference validation and real Kaggle checkpoint preflight. Further patches are justified only by a concrete failure from those runs.

## 2. Baseline reproduction

Before editing, local-safe pytest passed `234` tests in `36.16s`; statistical and artifact lanes passed `31` and `25`; the extended synthetic/gate lane passed `3`; notebook/registry/CVPR/forensic/V9 audits passed; compile/import/Ruff, critical mypy, firewall/privacy/release and diff checks passed. Full mypy reported exactly `111 errors in 34 files`. The paper compiled to five pages (179,907 bytes) with three non-fatal overfull boxes. The worktree already contained 87 modified, 83 deleted and 240 collapsed untracked entries with zero staged paths. A verified canonical archive did not yet exist. See `reports/CERTGEN_FINAL_HARDENING_BASELINE.md`.

## 3. Known findings

| # | Status | Root cause and repair | Files / tests | Remaining risk |
|---:|---|---|---|---|
| 1 | `CONFIRMED → REPAIRED` | Version checks lacked setup. Added compatible environment profiles, idempotent inspection/install, logged lock, restart and revalidation. | `environment_bootstrap.py`; focused bootstrap tests | Real Kaggle resolver behavior |
| 2 | `CONFIRMED → REPAIRED` | Network was disabled without complete caches. Added exclusive online-preflight/offline-cache policy, license blocker and hash/size/member manifest. | `model_assets.py`, model/feature registries; cache failure tests | Real auth/licenses/cache layouts |
| 3 | `CONFIRMED → REPAIRED` | Parent CUDA state could be forked. Added independent module workers with GPU pinning before lazy torch import and complete process logs/status. | `subprocess_orchestrator.py`, `workers/*`; crash/timeout/device tests | Real CUDA drivers/T4x2 |
| 4 | `CONFIRMED → REPAIRED` | Declared batch size hid per-image generation. Added capability-aware true batches, per-image generators and safe fallback contract. | `generation_runtime.py`; batch/seed tests | Adapter-specific real APIs |
| 5 | `CONFIRMED → REPAIRED` | Preprocessing YAML was not observed. Added exact expected/observed typed contract and runtime processor adapters/diff report. | `preprocessing_contract.py`, feature worker; mismatch tests | Real CLIP/DINO versions |
| 6 | `CONFIRMED → REPAIRED` | Existing outputs caused coarse refusal. Added explicit hash-bound resume/restart/force-new behavior, atomic samples and quarantine. | `run_state.py`, generation runtime; identity/mode tests | Long real interruptions |
| 7 | `CONFIRMED → REPAIRED` | Dispatcher routed through V6/V9 commands/notebooks. Replaced it with 19 canonical CVPR states/commands; legacy labels are mirrors only. | `v9_next_action.py`, `__main__.py`; CLI/V9 tests | Historical files remain noncanonical |
| 8 | `CONFIRMED → REPAIRED` | Real-run YAML depended on manual editing. Added registry/prior-import-derived preflight, generation, feature, family and runtime builders. | `prepare.py`; architecture contracts | External approvals/artifacts required |
| 9 | `CONFIRMED → REPAIRED` | Four audit tests launched full pytest inside default pytest. Marked them `integration_audit`; default excludes them, explicit lane remains. | `pyproject.toml`, four audit tests | Explicit integration lane is intentionally slower |
| 10 | `CONFIRMED → REPAIRED` | README/handbooks/status/ADE20K guidance conflicted. Unified canonical links/status/action and marked old handbook/report superseded. | README, final handbook, execution docs, safety inventory | Historical content is retained only as labeled context |
| 11 | `CONFIRMED → REPAIRED` | Export could contain caches/metadata/datasets and omit roots. Added deterministic allowlisted archive with extraction, import, privacy and non-Git test verification. | `release/archive.py`, archive tests | Consumer environments remain external |

The exact priority, file and risk ledger is `reports/CERTGEN_FINAL_HARDENING_REPAIR_CHANGELOG.md`.

## 4. New value upgrades

- Environment bootstrap: generation/features/preflight compatibility profiles, install logs, resolved lock and mandatory restart recheck.
- Asset policy: explicit network mode, complete portable cache manifests, pinned revisions and honest license blockers.
- Subprocess workers: one independent Python process per logical GPU with pre-import visibility and failure/timeout/rerun records.
- Batching/OOM: true capability-aware batches, deterministic per-sample seeds, atomic decode/hash validation and minimum-batch failure.
- Preprocessing proof: exact expected-versus-observed processor equality and machine-readable differences.
- Config builders: fail-closed preparation from registries and imported identities.
- Runtime calibration: measured seconds/image, batch, VRAM and cache time can replace labeled planning inputs.
- Fake runtime: actual two-worker generation/resume/ZIP/import/cache/metric/certificate/ranking/firewall path passes with synthetic-only labels.
- Archive export: deterministic clean path-preserving export and portable non-Git validation.
- Reproducibility fingerprint: benchmark/model/feature registries, preregistration, reference, assets, generation, features, family, code commit and environment bind into one fail-closed hash; paper-evidence certificates require it.

## 5. Notebook readiness matrix

| Notebook | Environment | Network/cache | Isolation | Batch/OOM | Resume | Preprocessing | Integrity/ZIP | Fixture/static | Real Kaggle | Risk |
|---|---|---|---|---|---|---|---|---|---|---|
| checkpoint preflight T4x2 | bootstrap/restart | online or complete offline, exclusive | subprocess | smoke calibration | model | capture/proof | yes | pass/pass | no | package/auth/driver |
| CIFAR generation 1k | bootstrap/restart | offline manifest | subprocess | true/halving | sample+shard | n/a | yes | pass/pass | no | real adapter/memory |
| generic generation | bootstrap/restart | offline manifest | subprocess | capability-aware | sample+shard | n/a | yes | pass/pass | no | adapter coverage |
| CIFAR features 1k | bootstrap/restart | offline extractor cache | subprocess | calibrated/fallback | extractor+shard | exact observed | yes | pass/pass | no | CLIP/DINO behavior |
| generic features | bootstrap/restart | offline extractor cache | subprocess | calibrated/fallback | extractor+shard | exact observed | yes | pass/pass | no | benchmark/extractor variance |

All rows include a disk guard, run identity, atomic status, process logs, deterministic archive and copy-back instructions. `real_kaggle_tested=false` for every row.

## 6. Verification

| Command | Exit | Result |
|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -m pytest -q` | 0 | `241 passed, 4 deselected` |
| `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -m pytest -q -m integration_audit` | 0 | `4 passed, 241 deselected` |
| Statistical six-file lane | 0 | `31 passed` |
| Artifact-contract six-file lane | 0 | `25 passed` |
| Runtime-hardening plus portable archive lane | 0 | `11 passed` |
| CVPR architecture/planner/extended/gates lane | 0 | `15 passed` |
| `python3 -m certgen synthetic-runtime --out-dir <new-temp-dir>` | 0 | 8 stages pass; fingerprint-bound certificate; synthetic only |
| `python3 -m compileall -q certgen tests` / import probe / `ruff check certgen tests` | 0 / 0 / 0 | pass |
| Critical mypy lane | 0 | no issues in 41 source files |
| `python3 -m mypy certgen` | 1 | exactly `111 errors in 34 files`, unchanged historical debt |
| Notebook / registry / CVPR / forensic / V9 audits | 0 | `5/5`, pass, `8/8`, `8/8`, `22/22` |
| Final execution audit | 0 | honestly `BLOCKED_MISSING_REFERENCE_SAMPLES` |
| Paper firewall / artifact registry / release safety | 0 | pass |
| `pdflatex ... main.tex` | 0 | 5 pages, 179,907 bytes, 3 non-fatal overfull boxes |
| Clean archive build/extract/import/portable test | 0 | probe `ARCHIVE_VERIFIED`, 688 members, portable `1 passed` |
| Private-path scan / `git diff --check` | 0 / 0 | pass |

Exact invocations, durations, evidence labels and output paths are in `reports/CERTGEN_FINAL_HARDENING_COMMAND_LEDGER.csv`. None of these checks is empirical model evidence.

## 7. Remaining blockers

| Class | State |
|---|---|
| `USER_INPUT` | Official or supported local CIFAR-10 source missing |
| `REAL_KAGGLE_RUNTIME` | Five canonical notebooks not run on Kaggle |
| `REAL_MODEL_LOAD` | Revisions/assets/auth/licenses not real-preflight validated |
| `REAL_GENERATION` | No real generated samples |
| `REAL_FEATURES` | No real observed extractor outputs/caches |
| `REAL_METRIC_REPRODUCTION` | No real immutable cache pair/target comparison |
| `REAL_CERTIFICATE` | No real family-bound certificate or ranking |
| `REAL_CVPR_EVIDENCE` | Paper firewall correctly blocks promotion |

## 8. Stop-building verdict

No further broad pre-execution upgrades are justified. The project must now execute the reference validation and real Kaggle checkpoint preflight. Continue only with narrow repairs supported by preserved real-run logs: bootstrap, adapter, asset cache, GPU, OOM, preprocessing, integrity or importer failures. P5 dashboards, new metrics, unrelated theory and paper-result prose are rejected.

## 9. Exact next action

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```
