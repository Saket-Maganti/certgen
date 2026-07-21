# CertGen Scale-Up and Stop Rules

Status: `PLANNING_ONLY`; `not_empirical_evidence`; `claim_allowed=false`.

## Governing rule

Scale only to answer a prespecified scientific question. Never add samples, comparisons, metrics, or benchmarks to force a decision or rescue a headline.

## Execution ladder

| Gate | Planned action | Required evidence to advance | Mandatory stop |
|---|---|---|---|
| G0 local integrity | Compile, tests, schemas, importer safety, paper firewall, synthetic statistical checks | all required local-safe gates pass; synthetic outputs remain non-evidence | any correctness, support, evidence-boundary, or artifact-integrity failure |
| G1 source preflight | Validate reference, licenses/terms, exact checkpoints or sample archives, immutable manifests | accepted source records and no unresolved blocking term | missing/ambiguous source, license, revision, hash, or independence contract |
| G2 1k integrity pilot | At most 1,000 samples per distribution / 500 raw units at block size one | cache, metric reproduction, null, obvious-gap, family, and certificate audits pass | partial data, wrong direction, support escape, duplication, plan drift, or invalid stream |
| G3 minimum scale | Up to 10,000 model samples per distribution / 5,000 raw units when a validated reference draw plan permits | G2 passes and additional budget answers a registered endpoint | valid crossing, model-row or draw-plan exhaustion, no-cost limit, or invalid assumption |
| G4 second benchmark | Execute the frozen AFHQ v2 candidate or logged FFHQ feasibility fallback | benchmark was selected before CIFAR results and all source gates pass | result-driven selection, insufficient independent sources, privacy/license blocker |
| G5 maximum breadth | Add one predeclared large-scale/archive-driven image family and literature reanalysis | minimum study is valid and breadth changes the scientific scope | infrastructure-only work, inaccessible data, or no claim-capable lineage |
| G6 conditional T2I | Implement and validate a matching conditional or IID marginal theorem and stream | formal proof, code, tests, and prospective protocol all pass | shared-prompt dependence handled only by prose or diagnostic e-values |

All scales and effort labels are planning values, not measured runtime or feasibility evidence.

## Per-comparison stopping

1. Freeze the seed/sample order, maximum budget, and Bonferroni level.
2. Monitor only the union-Hoeffding interval over valid disjoint-pair RBF contributions.
3. Stop at the first interval excluding zero and record CS units plus samples per distribution.
4. If no crossing occurs, right-censor at the frozen maximum.
5. Never restart the same comparison with fresh alpha, a new gamma, or a favorable extractor.
6. Never reuse reference rows ad hoc; repeated source IDs are allowed only through the precommitted IID-with-replacement draw plan.

For block size `b`, one CS unit consumes `2b` model draws and `2b` registered reference draw IDs. A larger generated pool is useless after an A/B provenance limit or the registered reference draw-plan horizon is exhausted.

## Stage advancement checks

Advance only when all answers are yes:

- source and license/terms approved for this use and release plan;
- exact model/sample identity and revision verified;
- independent rows and non-overlapping seed ranges verified;
- immutable manifest and hashes present;
- extractor and preprocessing lock complete;
- cache row identity, order, role, shape, and finiteness pass;
- independent metric reproduction passes;
- `[-3,3]` support and disjoint-pair construction pass;
- null and obvious-gap controls are audited;
- the full confirmatory family and Bonferroni alpha are frozen;
- failure/resume records are complete; and
- no claim-bearing value was used to select the next protocol.

## Scientific stop rules

- **Stop on a valid crossing:** do not spend more samples on that comparison for the primary endpoint.
- **Stop on invalidity:** assumption, provenance, cache, or metric failure yields `invalid_or_rejected`, not an undecided result.
- **Stop at the registered reference horizon:** do not extend or regenerate the draw plan after inspecting certificate values.
- **Stop on wrong-direction obvious-gap control:** quarantine claim outputs and diagnose before rerun.
- **Audit a null crossing:** it may be an alpha-level event, but result promotion pauses until lineage and multiplicity are confirmed.
- **Stop on plan drift:** a changed extractor, gamma, pair, seed range, family, or budget requires an amendment; post-inspection changes are exploratory.
- **Stop at no-cost boundary:** no paid API/cloud action; preserve a runnable handoff instead.
- **Stop adding infrastructure:** once the first real pilot can run safely, remaining work should be data execution, theory repair, or paper analysis—not another versioned wrapper.

## Pivot rules

| Observed registered outcome | Allowed response | Forbidden response |
|---|---|---|
| Maximum-budget undecided fraction below `0.05` | report it; test the preregistered efficiency/reproducibility story | search for harder pairs or change the metric to manufacture uncertainty |
| `0.05` to below `0.25` | present mixed decidedness and the full censoring curve | collapse to a binary success story |
| At least `0.25` | consider an uncertainty-audit headline after breadth and gates pass | generalize beyond the frozen family |
| Nearly all comparisons unresolved | report censoring; scale only within unique capacity | call models equivalent or tune bandwidth post hoc |
| Protocol directions disagree | report protocol dependence with family correction | select the favorable extractor/kernel |
| Second benchmark unavailable | use only the predeclared feasibility fallback before results | replace it after seeing CIFAR outcomes |

## Completion tests

Minimum-study completion requires two valid benchmark families, every frozen contestable pair and control accounted for, right-censoring-aware outputs, a simultaneous Bonferroni partial graph, and paper claim traces. Maximum-ceiling completion additionally requires a third image family and the frozen literature audit. Conditional text-to-image is not required unless its theory is repaired; without that repair it stays an explicit non-claim.

Current scale status: `G0_LOCAL_REPAIRS_IN_PROGRESS; G1_BLOCKED_REFERENCE_AND_CHECKPOINT_INPUTS`.
