# CertGen Maximum-Ceiling Repair and Upgrade Changelog

Every row is a local or synthetic contract upgrade. None is empirical evidence; all outputs retain `claim_allowed=false`.

| Upgrade | Motivation | Implementation | Tests/artifact | Readiness effect | Claim-surface effect |
|---|---|---|---|---|---|
| Transactional replacement | Eliminate stale mixed trees | Verified archive swap with Git preservation and rollback gate | Replacement audit | Clean fixed baseline | None |
| Provenance DAG | Make all downstream lineage content-addressed | Deterministic node/edge graph, hash/cycle/parent checks, DOT | `provenance graph/verify` | Detects stale or unregistered results | Claims require registered lineage |
| Stage doctor | Separate real blockers from local defects | Typed five-status diagnostic contract | `doctor` | Gives one actionable state | Prevents blocker laundering |
| Run capsules | Freeze execution inputs | Deterministic private/public ZIPs with study, profile, registry, assets, schemas, and locks | `capsule build/inspect/verify` | Reproducible handoff | No embedded evidence |
| Scale ladder | Prevent outcome-driven scaling | Frozen 1k/10k/50k entry, stop, repair, and promotion rules | `scale-plan` | Makes promotion prospective | Prohibits direction cherry-picking |
| Sensitivity matrix | Bound researcher degrees of freedom | Classified frozen lanes and validation | Sensitivity CSV/CLI | Precommits robustness work | Blocks post-hoc confirmatory growth |
| Resolution planner | Avoid clearly underpowered spend | Deterministic bounded synthetic streams | Four planning CSVs | Planning aid | Explicitly not empirical power |
| Failure rehearsal | Test recovery before GPU use | Sixteen fixture failure injections | Failure matrix | Verifies detector/recovery mapping | None |
| Replay planner | Minimize recomputation safely | Stage invalidation frontier and exact commands | Four replay artifacts | Preserves reusable valid work | No reuse across changed lineage |
| Certificate lineage | Make every decision inspectable | Profile, hypothesis, feature definition, controls, support, eligibility | Lineage card | Better reviewer traceability | Still separately gated |
| Ranking provenance | Preserve partial-order semantics | Direct/transitive provenance and unresolved/invalid outputs | Five ranking products | Rejects incomplete family and forced total order | Partial relation only |
| Cross-feature policy | Interpret representation disagreement prospectively | Consensus and representation-specific outputs | Six analysis products | Avoids false implementation alarms | Consensus requires all valid lanes |
| Compute accounting | Separate estimates and measurements | Four typed accounting classes and complete field contract | `accounting summarize` | Ready for real runtime ingestion | Estimates cannot become measurements |
| Claim matrix | Bind paper statements to artifacts | Fail-closed reviewer matrix consumed by firewall | Claims CSV/validator | Blocks premature paper injection | All empirical rows blocked |
| Figure/table contracts | Prevent fabricated visualization data | Eight lineage-gated JSON schemas | Fixture schema tests | Renderers can be connected after real import | Requires registered real artifacts |
| Optional lanes | Keep extensions non-blocking | Four inactive prospective registry rows | Optional registry validation | Minimum CIFAR pilot stays runnable | No support claim before preflight |
| Kaggle contracts | Harden dual-T4 handoff | Existing five canonical notebooks retained and re-audited | Notebook static and deterministic checks | Locally run-ready | Real Kaggle validation still required |
| Unified readiness | Eliminate conflicting guidance | Readiness, doctor, and next-action share artifact-driven command | CLI agreement tests | One exact next action | No evidence promotion |
