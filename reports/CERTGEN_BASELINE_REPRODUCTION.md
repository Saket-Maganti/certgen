# CertGen Baseline Reproduction

Baseline frozen: `2026-07-11` before forensic-audit repairs. This report distinguishes live reproduction from historical statements. It is not empirical model evidence and sets `claim_allowed=false`.

## Repository identity and safety snapshot

| Item | Live baseline |
|---|---|
| Repository | `.` |
| Git repository | yes |
| Branch | `master` |
| Commit | `bff335aa648fd19e2fa7e3cfea293a6ca519a68b` |
| Commit date | `2026-06-24T14:02:54+05:30` |
| Worktree | heavily dirty before this audit; 18 tracked files modified and at least 307 untracked files were recorded |
| Ignored inventory | 393 paths, dominated by interpreter/tool caches and `.DS_Store` |
| Files larger than 10 MiB | none found |
| Historical summary `certgenv1.md` | not present in the repository or supplied attachments |

All pre-existing tracked modifications, untracked V6–V9 files, raw ZIPs, manifests, and generated reports were treated as user-owned. No reset, clean, checkout, deletion, commit, upload, or remote execution was performed.

## Environment

`Python 3.11.9`; CertGen `0.5.0`; NumPy `2.4.4`; SciPy `1.17.1`; PyYAML `6.0.3`; pytest `9.0.2`; ruff `0.15.8`; mypy `2.1.0`; macOS/Darwin arm64. Default verification disabled CUDA and Python bytecode writes where applicable.

## Reproduced claims

| Historical statement | Live result | Classification | Notes |
|---|---|---|---|
| `183 tests passed` | `183 passed in 6.93s` | `VERIFIED_CURRENT` | Full default pytest suite, exit 0 |
| `V9 audit passed 22/22` | `22/22`, exit 0 | `VERIFIED_CURRENT` | The legacy V9 audit reproduces exactly |
| `V9_SUPERCHARGER_READY_BLOCKED_BY_INPUTS` | emitted live | `VERIFIED_CURRENT_BUT_TOO_BROAD` | Infrastructure audit passes, but later forensic review found notebook and theory defects it does not test |
| `BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE` | emitted live | `VERIFIED_CURRENT` | No accepted local source was found |
| `BLOCKED_MISSING_REFERENCE_SAMPLES` | emitted live | `VERIFIED_CURRENT` | Final execution audit and R1 readiness agree |

The historical numeric claims were not copied forward blindly; they were reproduced. Their interpretation is narrower than the old reports imply.

## Baseline command results

| Surface | Result | Classification |
|---|---|---|
| Package imports | pass | `VERIFIED_CURRENT` |
| Python compilation | pass | `VERIFIED_CURRENT` |
| Full pytest | 183 pass, 0 fail, 0 skip | `VERIFIED_CURRENT` |
| V7 execution-development audit | pass; blocker `BLOCKED_MISSING_REFERENCE_SAMPLES` | `VERIFIED_CURRENT_BUT_SHALLOW` |
| V9 notebook static analyzer | pass | `CONTRADICTED_BY_MANUAL_AUDIT` |
| V9 paper firewall | pass | `CONTRADICTED_BY_MANUAL_AUDIT` |
| V9 execution-supercharger audit | 22/22 pass | `VERIFIED_CURRENT_BUT_SHALLOW` |
| Final execution audit | `BLOCKED_MISSING_REFERENCE_SAMPLES` | `VERIFIED_CURRENT` |
| V5 release safety scan | pass | `VERIFIED_CURRENT_BUT_NARROW_SCOPE` |
| ruff | fail, 24 findings | `VERIFIED_CURRENT_FAILURE` |
| mypy | fail, 111 errors in 34 files | `VERIFIED_CURRENT_FAILURE` |
| paper compilation | fail on unescaped placeholder underscore | `VERIFIED_CURRENT_FAILURE`; repaired and recompiled successfully during this audit |

Exact timestamps, commands, exits, and log locations are in `reports/CERTGEN_COMMAND_LEDGER.csv`.

## Why two passing legacy gates were contradicted

The notebook analyzer checks for strings rather than execution semantics. Manual cell inspection found sequential GPU-0/GPU-1 subprocess calls instead of actual concurrent two-GPU work, unpinned installs, optional preflight, overwrite-prone resume behavior, and ZIP commands whose failure was ignored. Therefore “static analyzer passed” did not mean “production notebook contract passed.”

The paper firewall suppresses a forbidden phrase whenever a safe placeholder appears anywhere in the same file. It passed a section that said CertGen already “answer[s] with real benchmarks,” even though no real benchmark exists. That is a false negative, not paper evidence.

## Live artifact boundary

- No valid local CIFAR-10 reference source or materialized reference manifest exists.
- `registry/manifests/cifar10_r1_reference.jsonl` and `cifar10_r1_generated_pilot_1000.jsonl` contain only a newline.
- `registry/manifests/cifar10_r1_samples.jsonl` contains six planned rows whose local files do not exist.
- The 15 KiB generation-input ZIP is a code/config package with SHA-256 `20ef989fb8f1e54aa7013c143926c79e535948a23b30f341229cfa8678cba8db`; it contains no reference images or generated samples.
- No real checkpoint preflight output, generated sample package, Inception cache, CLIP cache, metric reproduction, sanity result, real certificate, undecided fraction, or samples-to-decision curve exists.
- No JSON under `data/` set `claim_allowed=true` at baseline.

## Baseline evidence-label defects

Smoke V3 certificates and their replay used `evidence_status=real_pilot_non_claim`, and smoke metric-reproduction outputs used `real_features_validated`. The accompanying `claim_allowed=false` prevented paper promotion, but the labels could mislead downstream tooling. These are `CONTRADICTED_BY_PROVENANCE`, not real pilot or real feature artifacts.

## Baseline scientific verdict

The repository had a potentially supportable disjoint-pair bounded RBF-MMD stream and conservative union-Hoeffding bound, but its default betting-grid confidence-sequence claim, directional e-BH narrative, metric-reproduction gate, and manuscript exceeded the checked theory. The baseline was therefore not ready to run a claim-bearing certificate. The forensic repair narrows the claim-capable route and keeps real execution blocked until a reference input and remaining pre-run contracts pass.

## Post-repair verification contrast

The final local-safe default suite passes `212` tests in `6.84s` with no failures or skips; the increase from 183 is due to new statistical, reference-sampling, cache, importer, notebook, evidence, and forensic regression tests. Python compilation, package imports, ruff, notebook static analysis, paper firewall, legacy V9 22/22, release safety, artifact-registry audit, and the new forensic 8/8 gate pass. The paper compiles to five pages with nonfatal overfull boxes.

Mypy remains a recorded failure: `111 errors in 34 files`, the same aggregate count as baseline. No configuration or ignore was added to conceal it. The final execution audit remains honestly blocked at `BLOCKED_MISSING_REFERENCE_SAMPLES`.
