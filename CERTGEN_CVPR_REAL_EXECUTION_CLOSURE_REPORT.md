# CertGen CVPR Real-Execution Closure Report

## 1. Executive verdict

Final status: `CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT`.

The real-execution path is continuous by local contract from reference validation through the first certified partial ranking. Every reproduced handoff defect is repaired: model and extractor preflight use real loaders when executed, generation and feature builders require complete imported preflight evidence, the shared ZIP schema is enforced by validators and importers, cache-v2 merge and family freeze exist, resume markers and final-ZIP recovery are validated, and the portable archive reproduces its declared local suite.

This pass did **not** validate or materialize real CIFAR data, load checkpoints, use CUDA, run Kaggle, generate samples, extract real features, compute real metrics/certificates, or create paper evidence. A 170,498,071-byte archive candidate exists at `cifar-10-python.tar.gz`, but its provenance, hash, and layout remain deliberately unvalidated. Therefore `claim_allowed=false` and the exact next command is:

```bash
python3 -m certgen validate reference --source cifar-10-python.tar.gz --explain
```

No further pre-run patch is justified without a concrete failure from that command or a later real-execution stage.

## 2. Baseline reproduction

The repair pass preserved the dirty user-owned worktree on branch `master` at `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`. Its inherited local baseline reproduced as `279 passed, 4 deselected`, with `4 passed, 279 deselected` in the recursive integration audit. The original closure baseline was `241 passed, 4 deselected`; the increase reflects already-present closure work plus new regressions.

The statistical lane passed 31 tests, the artifact-contract lane passed 25, notebook generation/static checks passed, Ruff passed, critical mypy passed, the paper compiled to five pages, and the paper firewall, privacy scan, release-safety audit, CVPR audit, forensic audit, and V9 compatibility audit passed. Full-project mypy reproduced the historical aggregate of `111 errors in 34 files` while checking 310 files. The pre-repair portable archive evidence was stale and was regenerated after the repairs.

## 3. Defect closure matrix

| Confirmed defect | Repair and current contract |
|---|---|
| Model preflight only inventoried assets | Family adapter performs local-path load, config verification, smoke decode/hash, throughput/VRAM capture, unload, and structured status |
| Extractor preflight absent | Processor/model load, observed preprocessing, finite/dimension smoke, asset identity, and batch calibration are required |
| Bulk GPU launches | Deterministic queues allow one active worker per GPU with isolated failure and timeout recovery |
| Frozen generation parameters were not reliably applied | Family adapters validate and apply the frozen prompt/class/seed/config semantics; requested/applied differences are recorded |
| Generic CFM routing was optimistic | Unsupported CFM and unknown adapters fail closed before packaging |
| Snapshot/cache and network-policy ambiguity | Canonical local snapshot identity/content hashes and independent dependency/asset network flags are enforced |
| Preflight handoff accepted weak reports | Generation and feature builders require matching run/config identity, successful load/smoke reports, valid calibration, and rebased imported assets |
| Feature preparation and merge were incomplete | Role-preserving packages, non-mixing shards, atomic cache-v2 merge, validation, and registration are implemented |
| Family builder used the wrong registry field | Frozen-study selection uses actual registry status/prospective fields and emits the full cartesian family |
| Notebook/import schemas drifted | `certgen.cvpr.output_schemas` is shared by output validation and import; root identity/config/status must agree |
| Legitimate checkpoint files were rejected | `.pt`, `.pth`, `.ckpt`, and `.model` are allowed while traversal and transient cache content remain blocked |
| Resume trusted marker existence | Marker schema, identity, relative output paths, SHA-256 values, and output bytes are validated; stale state is quarantined |
| Imported run IDs were rewritten | Canonical `run_identity.json` IDs survive validation/import when safe |
| Historical registry rows made the live audit fail | Explicit non-retained lifecycle states warn; fresh missing artifacts still fail |
| Final ZIP and portable archive recovery were incomplete | Valid reuse, rebuild, restart quarantine, force-new collision behavior, LICENSE/CITATION, and clean-extraction verification are present |

## 4. Real execution path

The singular path is: validate/materialize reference → freeze study → prepare and validate preflight input → run real model/extractor preflight on Kaggle T4×2 → validate/import output → ingest calibration → prepare/run/validate/import 1k generation → prepare/run/validate/import features → merge/validate cache-v2 → metric reproduction and sanity gates → freeze the Bonferroni family → certificate pilot → partial ranking → stop and interpret.

Builders consume only validated predecessor artifacts. Model and extractor caches are addressed by local paths with offline loading where required. Copied-back ZIPs are validated before import, imports preserve raw identity, and no stage silently upgrades a planning or fixture artifact to empirical evidence.

## 5. Notebook readiness

The five canonical CVPR notebooks pass deterministic regeneration and 5/5 static validation. The Phase‑1 diagnostic/preflight/generation/feature set also passes deterministic validation, and its launch audit passes 11/11. Queueing, split network policy, strict markers, shared output schema, runtime calibration, recovery, and claim-safe copy-back instructions are present. The builder-faithful synthetic rehearsal completes 27 stages and three certificates, but remains `synthetic_validation_only` and `not_model_evidence`.

Allowed wording: `run-ready by local contract; real Kaggle execution required`.

## 6. Verification

All commands below ran with `CUDA_VISIBLE_DEVICES=''`, `CERTGEN_CPU_ONLY=1`, and `PYTHONHASHSEED=0`; the command ledger records timestamps, durations, exit codes, and logs.

| Command | Exit | Result |
|---|---:|---|
| `python3 -m pytest -q` | 0 | 282 passed, 4 deselected |
| `python3 -m pytest -q -m integration_audit` | 0 | 4 passed, 282 deselected |
| statistical test lane | 0 | 31 passed |
| artifact-contract test lane | 0 | 25 passed |
| runtime-closure test lane | 0 | 27 passed |
| `python3 -m certgen.audit.cvpr_final_audit` | 0 | 8/8 passed |
| forensic audit | 0 | 8/8 passed |
| V9 compatibility audit | 0 | 22/22 passed |
| Phase‑1 Kaggle launch / CPU execution audits | 0 | 11/11 / pass |
| `python3 -m certgen audit notebooks` | 0 | 5/5 static pass |
| `python3 -m ruff check certgen tests scripts` | 0 | pass |
| critical touched-file mypy | 0 | no issues in 16 source files |
| `python3 -m mypy certgen` | 1 | historical debt: 111 errors in 34 files, 310 checked |
| `pdflatex ... paper/main.tex` | 0 | five-page document build |
| portable archive build/verification | 0 | 834 members, import pass, 12 portable tests, 5/5 notebooks, synthetic rehearsal pass |

The direct license-field inventory still reports `unknown` values in historical/template registry rows. Those fields are an explicit human approval boundary, not fabricated metadata; the release-safety audit passes and real package preparation remains fail-closed on required approvals.

## 7. Remaining blockers

| Boundary | Status |
|---|---|
| `USER_REFERENCE_INPUT` | local candidate present; official hash/layout validation required |
| `REAL_KAGGLE_MODEL_PREFLIGHT` | not run |
| `REAL_KAGGLE_EXTRACTOR_PREFLIGHT` | not run |
| `REAL_GENERATION` | not run |
| `REAL_FEATURE_EXTRACTION` | not run |
| `REAL_METRIC_REPRODUCTION` | blocked on validated real caches |
| `REAL_CERTIFICATE` | blocked on gates and frozen real family inputs |
| `REAL_CVPR_EVIDENCE` | absent; `claim_allowed=false` |

## 8. Stop-building verdict

No further broad or targeted pre-run infrastructure patch is justified. The repository is ready for the real CIFAR reference validation and first Kaggle preflight. Patch only a concrete observed failure in reference validation, model/extractor load, Kaggle environment, adapter semantics, OOM recovery, asset cache, output import, feature merge, metric reproduction, or evidence gating.

## 9. Exact next action

Run exactly, from the repository root:

```bash
python3 -m certgen validate reference --source cifar-10-python.tar.gz --explain
```

If validation fails, replace the candidate with the official CIFAR-10 Python archive and rerun the same command. Do not substitute fixture or generated data.
