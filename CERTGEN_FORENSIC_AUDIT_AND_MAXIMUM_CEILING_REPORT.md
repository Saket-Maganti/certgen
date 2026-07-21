# CertGen Forensic Audit, Scientific Repair, and Maximum-Ceiling Report

Audit date: 2026-07-11. Repository evidence boundary: `claim_allowed=false`.

## 1. Executive verdict

**Top-level status: `LOCAL_RESEARCH_CORE_VALID_BLOCKED_BY_REFERENCE_INPUT`.**

CertGen is now a conditionally valid bounded-kernel decision and evaluation-audit implementation. Its one claim-capable statistical route compares two fixed generator populations against a declared reference through an L2-normalized RBF-MMD-squared difference stream, a conservative union-Hoeffding confidence sequence, first-crossing decisions, and Bonferroni family control.

It is not metric-agnostic, not a validated model-ranking system, not a completed benchmark, and not a submission draft. It contains no claim-capable empirical result.

The historical `V9_SUPERCHARGER_READY_BLOCKED_BY_INPUTS` label was directionally correct about the missing reference but inaccurate as a readiness claim. Its 22/22 audit reproduced, yet it did not detect invalidly broad betting/e-BH theory, a weak metric-reproduction gate, sequential rather than concurrent notebook work, unsafe/weak resume and ZIP patterns, misleading evidence labels, or a paper-firewall false negative. The repaired local core is substantially narrower and more defensible.

The statistical core is valid **conditional on** the recorded stream assumptions. No real artifact has established those assumptions. Local execution cannot advance past reference validation; checkpoint preflight must not start yet.

Exact blocker: no accepted CIFAR-10 source and a zero-row reference manifest.

User action: place the official archive at `data/sources/cifar-10-python.tar.gz`.

Exact next command:

```bash
python3 -m certgen validate reference \
  --source data/sources/cifar-10-python.tar.gz \
  --explain
```

The maximum realistic paper is a prospective, multi-family generative-model evaluation audit with reproducibility gates. A minimum credible version could fit AISTATS, WACV, or TMLR depending on the finding; a NeurIPS/ICML/ICLR/CVPR main-track attempt requires maximum empirical breadth/consequence and remains high risk because the statistical ingredients are prior art and direct 2025 generative-comparison work exists.

## 2. Verified repository state

| Item | Verified current state |
|---|---|
| Branch / commit | `master` / `bff335aa648fd19e2fa7e3cfea293a6ca519a68b` |
| Worktree | heavily dirty before audit: 18 tracked modifications and at least 307 untracked files; final tree has 86 tracked changes and 368 untracked files after repairs; preserved without reset/clean/delete/commit/push |
| Package | `certgen` 0.5.0, Python >=3.10; canonical `python3 -m certgen` interface added |
| Baseline tests | exactly `183 passed in 6.93s`, 0 skips |
| Final tests | `212 passed in 6.84s`, 0 failures, 0 skips |
| Baseline audits | V9 22/22 pass, V7 pass/block missing reference, final audit block missing reference; several were shallow |
| Final forensic audit | 8/8 coherence checks pass |
| Notebooks | strengthened static contract passes all 3 V9 notebooks; no Kaggle execution |
| Data | no accepted CIFAR source; reference/generated canonical manifests have 0 rows; six planned rows point to missing files |
| Artifacts | 32 NPZ arrays are smoke fixtures; one code/config generation ZIP, no images; one planning registry entry |
| Evidence | no real preflight, generation, features, reproduction, controls, certificate, decidedness, stopping curve, or paper evidence |
| Paper | bounded-kernel scaffold, explicit missing-result placeholders; 5-page PDF compiles with nonfatal overfull boxes |
| Release | proposed surface only; LICENSE and CITATION metadata absent; no remote publication performed |
| Machine inventory | 1,005 files: 636 tracked, 368 untracked, 1 retained ignored scientific artifact, 170 generated-class, 580 legacy-class |

The machine inventory is in `reports/CERTGEN_REPOSITORY_INVENTORY.csv` and `.json`. It distinguishes current/legacy, source/generated, evidence class, release safety, tracked/ignored state, and action.

## 3. Discrepancies from historical summary

`certgenv1.md` was not present in the repository or attachments. The historical statements embedded in the audit prompt were treated as reported claims.

| Reported/history-derived statement | Live finding | Classification |
|---|---|---|
| 183 tests passed | reproduced exactly at baseline | `VERIFIED_CURRENT` at baseline |
| V9 passed 22/22 | reproduced exactly | `VERIFIED_CURRENT_BUT_SHALLOW` |
| ready except inputs | false as a scientific/safe-run interpretation | `CONTRADICTED_BY_FORENSIC_AUDIT` |
| notebook analyzer pass means production-ready | baseline analyzer missed semantic defects | `CONTRADICTED_BY_MANUAL_AUDIT` |
| paper firewall pass means claims are safe | forbidden real-benchmark sentence passed | `CONTRADICTED_BY_REGRESSION_CASE` |
| default betting CS is anytime-valid | finite-grid continuum inversion proof absent | `CONTRADICTED`; demoted |
| empirical-Bernstein route is time-uniform | no mapped theorem for formula | `CONTRADICTED`; demoted |
| e-BH supports directional ranking under continuous monitoring | current point-null/fixed-time scope is narrower | `CONTRADICTED`; blocked |
| metric-agnostic certificate framework | only bounded RBF-MMD route is claim-capable | `CONTRADICTED`; title rewritten |
| metric reproduction passed enough to unlock pilot | status was not bound to exact real inputs/specification | `CONTRADICTED`; hard gate repaired |
| smoke artifacts have real-pilot/real-feature status | provenance is fixture/synthetic | `CONTRADICTED_BY_PROVENANCE`; relabeled |
| CIFAR is the only blocker | immediate blocker yes, but later A/B provenance, cache, reproduction, controls, and family gates also remain | `PARTIALLY_TRUE_TOO_BROAD` |
| paper ready except results | paper lacked correct scope/closest-work framing and failed to compile | `CONTRADICTED`; repaired scaffold only |

## 4. Scientific-contribution audit

Current thesis: point-estimate generator comparisons should be recast, under one prospectively locked bounded-kernel protocol, as simultaneous anytime-valid directional edges or right-censored unresolved outcomes.

Strongest contribution: a prospective evaluation methodology tying optional-stopping-safe decisions to immutable source, cache, reproduction, multiplicity, and paper gates, followed by a real audit of decidedness and partial rankings.

Weakest historical claim: “metric-agnostic.” The implementation cannot certify FID/FD-DINOv2 or polynomial KID and has not validated a general metric interface theorem.

Closest work includes MMD/KID and CMMD evaluation, bounded-mean confidence sequences, sequential betting two-sample tests, e-BH, generative-evaluation sensitivity studies, and Gao–Sun–Su (2025), which directly studies uncertainty-quantified relative generator comparison on real image/text tasks. CertGen has no new sequential theorem at present.

Remaining novelty delta:

1. sample-only bounded-kernel comparison rather than requiring model density;
2. time-uniform monitoring and first-crossing/censoring;
3. prospective family-wise directional partial rankings;
4. same-lineage artifact and claim gates; and
5. a consequential prospective real-model audit.

Items 1–4 are method/protocol engineering until item 5 exists. The paper must be framed primarily as an evaluation audit and secondarily as a reproducibility protocol. Detailed primary sources and overlap are in `docs/research/CERTGEN_NOVELTY_FORENSIC_AUDIT.md` and the closest-work CSV.

## 5. Statistical audit

### Estimand and stream

For fixed feature map, preprocessing, L2 normalization, positive RBF `gamma`, model distributions `P_A/P_B`, and reference target `P_R`:

```text
Delta_AB = MMD_k^2(P_A,P_R) - MMD_k^2(P_B,P_R).
```

Negative means A is closer to the declared reference under this protocol; positive means B is closer. It is not universal quality.

One raw unit uses disjoint pairs from A, B, and R. The shared reference self-kernel cancels, leaving three nonnegative and three subtracted RBF terms, hence support `[-3,3]`. Under mutually independent IID/conditionally mean-stationary registered draws, its expectation is `Delta_AB`.

### Verdicts

| Question | Verdict |
|---|---|
| Estimand/algebra | `VERIFIED_CURRENT_CONDITIONAL` |
| Boundedness | `VERIFIED_CURRENT`: `[-3,3]` for bounded RBF path |
| Union-Hoeffding CS | `VERIFIED_CURRENT_CONDITIONAL`; summable error schedule gives time-uniform coverage |
| Optional stopping | valid at first boundary crossing under the same assumptions |
| Blocking | non-overlapping block means preserve bounds/mean; sample accounting repaired |
| Bandwidth | default fixed `gamma=0.5`; custom/data-driven choices blocked without prospective lock |
| Fixed reference | real route requires validated IID-with-replacement draw plan over frozen empirical population |
| Finite-grid betting | `SYNTHETIC_DIAGNOSTIC_ONLY`; continuum coverage open |
| Empirical Bernstein | `DIAGNOSTIC_ONLY`; theorem mapping open |
| Point-null e-value/e-BH | narrow fixed/local scope; no direction/global adaptive ranking |
| Bonferroni | primary simultaneous directional family route; cross-comparison independence not required |
| FID/FD/KID | descriptive-only under current theory |

One raw contribution consumes two samples from each role (six feature rows). Unresolved stopping time is right-censored at the maximum budget. A mean among decided comparisons alone is prohibited.

Unresolved proof/realization obligations: A/B independence and precommitment; actual reference plan/cache validation; duplicate image/cross-role lineage audit; custom bandwidth lock; complete higher-axis family manifest; real hash-bound metric reproduction; global/directional e-value theory; and online rather than retrospective compute-saving evidence.

## 6. Empirical-design audit

A 1k CIFAR lane is an integrity pilot, not a paper. The minimum credible study is a prospectively frozen two-image-family audit: CIFAR-10 plus a feasibility-selected higher-resolution family, provisionally AFHQ v2 with FFHQ as a pre-result fallback only after access/license/model-source checks. At least three recognized independent systems/sample sources per family are the target where feasibility permits; all unordered registered pairs enter.

Required taxonomy:

- reference-split and same-checkpoint independent-seed null controls;
- severe corruption obvious-gap controls;
- a frozen intermediate corruption ladder;
- contestable real model pairs selected without outcomes;
- deterministic extraction/shard reproduction checks; and
- prospectively declared extractor/kernel/preprocessing sensitivities.

Planning budgets are 1,000 and up to 10,000 model samples per distribution (at block size one, at most 500 and 5,000 raw units). They are not measurements. The reference uses distinct precommitted draw IDs sampled with replacement from a frozen empirical population; source IDs may recur only through that plan.

Primary outcomes: decided/undecided fraction by budget, full right-censored stopping distribution, controlled false-direction events, valid/invalid denominator, partial-ranking completeness, and protocol disagreement. Measured compute savings require online logs.

Prospective pivots prevent result fishing. A near-zero undecided fraction weakens the proposed headline; the study must report that outcome and may pivot only to registered early-decision/reproducibility questions. The literature audit uses a frozen paper sampling frame and only reanalyzes provenance-complete archives; it never reconstructs a certificate from a published point estimate.

## 7. Engineering audit

The package has reasonable module boundaries but is surrounded by extensive V1–V9 reports, prompt packs, configs, and wrappers. These were preserved, classified as legacy where appropriate, and excluded from the proposed public surface. New work should use `python3 -m certgen` rather than create another version layer.

Implemented improvements:

- canonical status/next-action/reference/import/audit CLI;
- atomic, non-overwriting, resource-bounded, allowlisted ZIP extraction;
- append-only artifact registry with SHA-256 verification;
- official CIFAR tar MD5/member validation, restricted pickle loading, privacy-safe manifests, and inaccessible-path reporting;
- immutable checkpoint/extractor revisions and resolved extractor metadata;
- two-GPU concurrent notebook workers, exact preflight dependency, deterministic shards, validated resume, atomic statuses, logs, and integrity manifests;
- canonical cache-v2 validation/migration; and
- offline default tests plus explicit statistical/artifact lanes.

Remaining engineering debt: no hosted CI; baseline mypy debt; multiple legacy schemas/wrappers; no clean-machine install/reproduction; no LICENSE/CITATION; real source/license/auth behavior untested; and no real import. Lint/type results are reported, not hidden or weakened.

## 8. Paper audit

Primary identity: generative-model evaluation methodology/audit. Secondary: reproducibility protocol. The working manuscript title is bounded-kernel rather than metric-agnostic.

The claim hierarchy separates conditional method statements from entirely missing empirical claims and explicit non-claims. The manuscript was repaired to state the estimand, `[-3,3]` stream, union-Hoeffding/Bonferroni route, descriptive metric boundary, and absence of results. The results section remains a placeholder and the firewall now catches the known false-negative pattern.

Eight evidence-dependent figures and ten table roles are specified without generating fake plots. Four adversarial reviewer simulations agree that current rejection is mandatory: no empirical contribution exists. Fatal risks are invalid sampling assumptions, direct prior overlap, CIFAR-only evidence, and untraceable paper cells.

Current readiness: `SCAFFOLD_COMPILES_NO_EMPIRICAL_RESULTS`, not a submission draft.

## 9. Repairs implemented

The complete finding/root-cause/file/test ledger is `reports/CERTGEN_REPAIR_CHANGELOG.md`. Highest-impact repairs are:

| Severity | Finding | Change | Verification |
|---|---|---|---|
| P0 | unsupported default sequential method | demoted betting/EB paths; made union-Hoeffding default | focused CS/certificate tests |
| P0 | wrong/loose stream implementation contract | direct cancellation, `[-3,3]`, fixed gamma, sample metadata | stream/bound tests |
| P0 | fixed-reference sampling gap | precommitted with-replacement plan and hard gate | draw-plan tests |
| P0 | ambiguous feature identity | cache-v2 validator/migrator and real gate | cache contract tests |
| P0 | weak reproduction/evidence gates | exact hash/spec binding and input-derived labels | metric/evidence tests |
| P0 | paper claim leakage | claim-scoped firewall and manuscript rewrite | regression/firewall/build |
| P0 | unsafe ZIP/import path | safe atomic extractor and append-only registry | malicious archive/tamper tests |
| P0 | notebook semantic defects | real concurrency, revisions, resume/integrity/failure rules | strengthened analyzer |
| P1 | fragmented interface | canonical module CLI and exact-action engine | CLI tests/live commands |

## 10. Verification results

Baseline commands, timestamps, durations, exits, and logs are in `reports/CERTGEN_COMMAND_LEDGER.csv`. Final results are refreshed after the consolidated audit artifacts exist.

| Command | Exit | Result |
|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -m pytest -q` | 0 | 212 passed in 6.84s; 0 failed; 0 skipped |
| `python3 -m compileall -q certgen tests` | 0 | pass |
| `ruff check certgen tests` | 0 | all checks pass after 27 findings were repaired |
| `mypy certgen` | 1 | 111 errors in 34 files; same aggregate debt as baseline, not hidden |
| `python3 -m certgen audit notebooks` | 0 | 3/3 static contract pass; not execution evidence |
| `python3 -m certgen audit paper` | 0 | firewall pass after repairs |
| `python3 -m certgen audit artifact-registry` | 0 | 1 planning entry hash-valid |
| canonical broad reference validation | 2 expected | 0 accepted / 224 rejected; missing input |
| `pdflatex ... main.tex` | 0 | 5 pages, 178819 bytes; four nonfatal overfull-box messages |
| forensic coherence audit | 0 | 8/8 checks pass |

No default test intentionally downloads a dataset/model or uses CUDA. Any final skips are reported explicitly rather than interpreted as passes.

## 11. Remaining blockers

**User-supplied input:** accepted CIFAR-10 source.

**External execution:** real T4x2 checkpoint preflight, generation, and feature extraction; no remote action was authorized or run.

**Unresolved real assumptions/theory:** A/B IID/precommitment evidence; real reference draw plan; same-lineage cache/reproduction; global/directional e-BH if desired; betting/EB proof obligations; conditional text-to-image stream.

**Unavailable evidence:** every real model result, control, certificate, censoring curve, ranking, runtime, and paper cell.

**Paper breadth:** minimum second family, closest-method comparison, sensitivity, independent reproduction, and possibly a systematic literature/artifact audit.

The immediate status is blocked by reference input even though later blockers are already known. Supplying CIFAR does not automatically make the project pilot-ready.

## 12. Prioritized roadmap

The full owner/location/input/output/dependency/effort/compute/evidence/permission/completion ledger is `reports/CERTGEN_REMAINING_WORK_PRIORITIZED.md`.

- **P0:** validate/materialize reference, freeze draw plan, review checkpoint source/license, rebuild stale package.
- **P1:** preflight, generate/import, extract/import/cache-v2, reproduce metric, run controls, freeze family, run pilot.
- **P2:** apply pivot rule, independently reproduce, execute minimum second family.
- **P3:** closest-method baseline, breadth/sensitivity, literature audit, online resource logs, paper/release claim trace.
- **P4:** bounded maintenance such as mypy cleanup or a genuinely proved stronger CS.
- **REJECTED:** new version layers, forced ranking/dashboard, inherited metric guarantees, automatic downloads, or post hoc benchmark search.

## 13. Venue and ceiling analysis

| Venue | Current suitability | Minimum credible version | Strong / maximum version | Likely objection |
|---|---|---|---|---|
| NeurIPS E&D | none | broad two-family audit plus artifacts | multi-family + literature audit | no consequential benchmark finding |
| NeurIPS main | none | below likely bar | consequential multi-domain audit + closest baseline/theory depth | established ingredients/direct overlap |
| ICML | none | strong method/evidence required | sharper inference or exceptional audit | incremental specialization |
| AISTATS | none | valid two-family statistical study | stronger CS/power plus audit | generative breadth too thin |
| ICLR | none | modern meaningful families | broad reproducible ranking consequence | CIFAR-centric relevance |
| CVPR | none | strong modern vision breadth | compelling semantic/visual audit | known statistics, weak vision contribution |
| WACV | none | complete two-family vision study | broader release/sensitivity | novelty/scale |
| TMLR | none | rigorous complete methodology study | deep long-form audit/capsule | no empirical conclusion yet |
| JMLR | none | major statistical depth | new theory + exhaustive evidence | theory contribution too narrow |
| TPAMI | none | mature broad body of work | comprehensive multi-year study | far below journal scope |

These are strategic fit judgments, not acceptance probabilities.

## 14. Exact critical path

1. **First real certificate:** user reference -> materialize/freeze draw plan -> preflight -> generation/import -> features/import/cache-v2 -> reproduction -> controls -> family -> pilot.
2. **Minimum credible paper:** first pilot -> preregistered pivot -> second image family -> all pairs/controls -> closest baseline -> sensitivity -> independent reproduction -> gated paper.
3. **Strong main-track paper:** minimum study -> third family or valid modern extension -> literature/artifact audit -> measured online resource impact -> consequential partial-ranking result.
4. **Maximum ceiling:** strong study plus a material proved inferential extension and comprehensive public capsule.

The executable per-stage gates are in `docs/CERTGEN_EXECUTION_CRITICAL_PATH.md`.

## 15. Stop-building verdict

Stop adding generic infrastructure now. The statistical core, reference/cache contracts, safe import, notebooks, evidence firewall, tests, canonical interface, and next-action engine are sufficient to expose the first real input/run failures safely.

Do not build V10/V11, another prompt pack, a forced-ranking dashboard, new metric wrappers without proofs, or more planning reports. Locally repair only a concrete defect surfaced by the next real stage. All remaining scientific progress requires user data, checkpoint loading, external execution, or real evidence.

## 16. Final handoff

```text
Repository: /Users/saketmaganti/Projects/certGen
Status: LOCAL_RESEARCH_CORE_VALID_BLOCKED_BY_REFERENCE_INPUT
Branch/commit: master @ bff335aa648fd19e2fa7e3cfea293a6ca519a68b
Worktree: heavily dirty before audit; preserve everything; no reset/clean/commit/push
Claim-capable core: fixed L2 RBF gamma=0.5, disjoint-pair Delta=MMD2(A,R)-MMD2(B,R), support [-3,3], union-Hoeffding, first crossing, Bonferroni
Blocked methods: betting-grid CS, empirical Bernstein, directional/global e-BH, FID/FD/KID certification
Evidence: none; all model/reference/result stages missing
Immediate user file: data/sources/cifar-10-python.tar.gz
Exact command: python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
Success: READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION, then rerun python3 -m certgen next-action --write
Do not call tests/notebooks/manifests evidence; keep claim_allowed=false
Read first: docs/CERTGEN_SINGLE_FILE_HANDOFF.md, reports/CERTGEN_CURRENT_STATE.json, reports/CERTGEN_EVIDENCE_BOUNDARY_AUDIT.md
```
