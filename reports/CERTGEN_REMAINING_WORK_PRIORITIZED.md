# CertGen Remaining Work — Prioritized and Bounded

## MUST FIX BEFORE ANY RUN

No additional generic infrastructure is required before reference validation. The user must supply a source. Before any external checkpoint/generation run, freeze source/license acceptance, exact checkpoint registry, package revisions, and rebuild the stale generation input package from the repaired source tree.

| Priority | Task | Owner | Location | Input | Output | Dependency | Effort | Compute | Evidence produced | Claim permission | Completion test |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P0 | validate and materialize CIFAR reference | user + local researcher | `data/sources`, reference manifest | accepted source | 10k-row manifest/provenance | user file | short local | CPU | reference/cache artifact only | false | source, count, dimension, ID, hash, license gates pass |
| P0 | build/freeze reference draw plan | statistician | run registry | frozen reference IDs and budget | hash-bound plan | materialized reference | short local | CPU | design contract | false | deterministic validation and cache order match |
| P0 | freeze checkpoint license/auth and rebuild package | ML engineer | checkpoint registry/package | exact source/revisions | reviewed registry + new ZIP hash | reference accepted | hours | CPU | planning/run input | false | package audit passes and stale hash is retired, not overwritten |

## MUST DO DURING FIRST REAL RUN

| Priority | Task | Owner | Location | Input | Output | Dependency | Effort | Compute | Evidence produced | Claim permission | Completion test |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | checkpoint preflight | ML engineer | Kaggle notebook | exact registry | immutable preflight ZIP/logs | package | 1 session | external T4x2 | run log only | false | every exact revision passes image checks and safe import |
| P1 | 1k generation and safe import | ML engineer | generation notebook/importer | preflight | complete sample manifests/images | preflight | 1 session | external T4x2 | pilot sample artifacts | false | six shards, seeds/hashes/dimensions, integrity/import pass |
| P1 | feature extraction and cache-v2 validation | ML engineer | feature notebook/local cache gate | validated samples/reference | canonical feature caches | generation | 1 session | external T4x2 + CPU | cache artifacts | false | all roles/extractors match manifests and v2 contract |
| P1 | exact metric reproduction | evaluation researcher | metric gate | exact caches/spec/plan | reproduction JSON | cache-v2 | hours | CPU | sanity artifact | false | independent/trusted tolerance and every hash match |
| P1 | real null and obvious-gap controls | statistician + evaluation researcher | preregistry/certificate runner | approved caches/control transforms | trajectories | reproduction | hours | CPU | sanity artifacts | false | expected controls pass without exclusions |
| P1 | freeze Bonferroni family and run pilot | statistician | family ledger | all eligible pairs/axes | certificates + censored aggregation | controls | hours | CPU | pilot artifacts | false pending paper gate | full denominator and first-crossing audit pass |

## MUST DO AFTER FIRST PILOT

| Priority | Task | Owner | Location | Input | Output | Dependency | Effort | Compute | Evidence produced | Claim permission | Completion test |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P2 | apply preregistered pivot/scale rule | PI/statistician | scale rules | complete pilot | go/stop/pivot decision | pilot | hours | CPU | decision record | false | rule applied without outcome-selected pairs |
| P2 | independent clean-machine reproduction | independent researcher | public capsule | immutable pilot ZIPs | reproduction report | pilot | day | CPU/external as needed | reproducibility evidence | conditional | hashes/results reproduce or discrepancies disclosed |
| P2 | execute minimum second family | evaluation team | frozen registry | feasibility-approved sources | complete second-family audit | pre-result freeze | days | external + CPU | empirical evidence candidate | gated | same full lineage and controls pass |

## REQUIRED FOR MAIN-TRACK PAPER

| Priority | Task | Owner | Location | Input | Output | Dependency | Effort | Compute | Evidence produced | Claim permission | Completion test |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P3 | closest-method comparison including Gao–Sun–Su | method team | study registry | mutually applicable comparisons | fair baseline table | real study | days | CPU/external | empirical candidate | gated | assumptions/access differences stated and protocol frozen |
| P3 | multi-family breadth and protocol sensitivity | evaluation team | maximum study | frozen sources/protocols | figures/tables/partial rankings | minimum study | weeks | external + CPU | empirical candidate | gated | all registered cells and multiplicity accounted |
| P3 | systematic literature/artifact audit | two reviewers | literature schema | frozen sampling frame | adjudicated dataset/report | protocol freeze | weeks | CPU | audit evidence | gated | reproducible selection, two-reviewer QC, denominators |
| P3 | measured online resource savings | ML engineer | run ledger | online early-stop-capable run | measured sample/time/resource logs | live integration | days | external | compute evidence | gated | immutable logs; no retrospective substitution |
| P3 | paper claim trace and public release | authors/release reviewer | paper/release | approved artifacts | compiled manuscript/capsule | complete evidence | days | CPU | paper/release | only approved claims | every cell traces, firewall/build/secrets/license pass |

## OPTIONAL NICE-TO-HAVE

| Priority | Task | Owner | Location | Input | Output | Dependency | Effort | Compute | Evidence produced | Claim permission | Completion test |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4 | reduce mypy debt module by module | maintainer | `certgen/` | final mypy ledger | typed clean modules | none | days | CPU | software quality only | false | no new ignores; chosen module clean |
| P4 | deprecate legacy wrappers visibly | maintainer | commands/docs | canonical interface | thin routing shims | first run | days | CPU | maintenance only | false | no copied core logic and docs point canonical |
| P4 | prove/implement stronger CS | statistician | theory/stats | applicable theorem | tested method | empirical need | research | CPU | method evidence | conditional | proof mapping, coverage/type-I and power suite pass |

## DO NOT BUILD / REJECTED

- V10/V11 or another broad prompt-pack layer.
- A total-ranking UI before simultaneous partial edges exist.
- More metrics inheriting guarantees by name.
- Automatic data/model downloads in default tests.
- A custom distributed training/orchestration system for two independent GPU workers.
- A dashboard that hides missing/invalid registered members.
- A paper result generator that bypasses the evidence ledger.
- Post hoc benchmark/model-pair search to rescue the headline.

The shortest next action remains the single reference-validation command in `docs/CERTGEN_EXACT_NEXT_ACTION.md`.
