# CertGen CVPR Complete Execution and Run Handbook

> Superseded by `CERTGEN_CVPR_FINAL_RUN_READY_EXECUTION_HANDBOOK.md`.

> **SUPERSEDED — HISTORICAL PRE-EXECUTION SNAPSHOT.** Do not execute commands from this file. The canonical runbook is `CERTGEN_CVPR_RUN_READY_EXECUTION_HANDBOOK.md`.

`planning_only` · `not_empirical_evidence` · `claim_allowed=false`

## A. Current exact status

Top-level status: `CVPR_PREEXECUTION_READY_BLOCKED_BY_REFERENCE_INPUT`. Verified pre-build baseline: 212 default tests, 22 documented statistical-lane tests, and 18 documented artifact-lane tests. Final local verification: 234 tests, 31/31 statistical-lane checks, 25/25 artifact-contract checks, 11/11 extended CVPR synthetic/gate checks, 8/8 CVPR checks, 8/8 forensic checks, 22/22 V9 compatibility checks, and 5/5 canonical notebook static checks; compilation/import/ruff/paper/firewall/privacy/artifact audits pass. Full mypy retains exactly 111 historical errors in 34 files; the 25-file critical new-code lane passes. There is no validated real reference, checkpoint load, generation, feature cache, metric/sanity result, certificate, ranking, or paper evidence.

Exact next command:

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```

Expected output: `data/results/v9_cifar_reference_onramp.json`; success: `READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION`. No download occurs.

## B. Hardware and environment assumptions

- Verified local environment: macOS/CPU, Python 3.11.9, NumPy 2.4.4, SciPy 1.17.1, PyYAML 6.0.3, pytest 9.0.2; no GPU or network for validation/certification.
- Kaggle: two visible T4 GPUs requested; explicit, logged single-T4 fallback only when approved.
- Kaggle dependencies are pinned to torch 2.7.1, torchvision 0.22.1, diffusers 0.34.0, transformers 4.53.2, accelerate 1.8.1, safetensors 0.5.3, timm 1.0.16, Pillow 11.2.1, NumPy 2.0.2, and PyYAML 6.0.2. The notebook records observed versions and fails on a mismatch.
- Disk: at least 10 GiB free in `/kaggle/working` at bootstrap, plus calculated model/cache/image/ZIP headroom. RAM and VRAM are configuration/model dependent; verify both T4 devices and lower batch size only through a new frozen configuration if the preflight shows a limit.
- Network: off when uploaded caches suffice; on only when source license/auth permits and the registry records it.
- Dependencies: exact pinned versions are captured and compared; a mismatch blocks execution.
- Runtime values below are planning estimates, hardware-dependent, and not empirical project results.

## C-D. Complete run classification

The authoritative 21-field table is reproduced here and stored at `reports/CERTGEN_CVPR_RUN_CLASSIFICATION.csv`. Run IDs follow `<benchmark>__<stage>__<scale>__<feature>__<config-hash>__<timestamp>`.

```csv
run_id_template,run_name,class,priority,purpose,location,CPU_or_GPU,GPU_count,input,output,prerequisites,command_or_notebook,planning_runtime,planning_disk,planning_RAM,planning_VRAM,resumable,failure_recovery,evidence_class,claim_permission,completion_test
local__validation__current__none__hash__timestamp,LOCAL_CPU_VALIDATION,A,P0,local safety,local,CPU,0,repo,audit,none,python3 -m certgen audit cvpr,minutes,small,low,none,yes,repair exact failing gate,planning_only,false,audit pass
cifar10__reference__test__none__hash__timestamp,LOCAL_CPU_REFERENCE,B,P0,reference manifest,local,CPU,0,official source,10k manifest,user source,python3 -m certgen materialize reference --source <path>,minutes,under 1 GiB,low,none,idempotent identical,preserve source and report rejected layout,cache_artifact,false,10000 validated rows
cifar10__preflight__tiny__none__hash__timestamp,KAGGLE_T4X2_PREFLIGHT,C,P1,real load,Kaggle,GPU,2,preflight package,preflight ZIP,reference+registry,certgen_cvpr_checkpoint_preflight_t4x2.ipynb,5-30 minutes,model dependent,Kaggle dependent,T4 dependent,per model,rerun failed model only under same hash,run_log_only,false,all model status pass
cifar10__generation__1k__none__hash__timestamp,KAGGLE_T4X2_GENERATION,D,P1,1k samples/model,Kaggle,GPU,2,validated preflight,generation ZIP,preflight import,certgen_cvpr_cifar10_generation_t4x2_1k.ipynb,30 minutes-3 hours,model/image dependent,Kaggle dependent,T4 dependent,per shard,quarantine invalid shard; rerun exact shard,pilot_only,false,complete unique manifest
cifar10__features__1k__feature__hash__timestamp,KAGGLE_T4X2_FEATURE_EXTRACTION,E,P1,three feature spaces,Kaggle,GPU,2,images+locks,feature ZIP,generation import,certgen_cvpr_feature_extraction_t4x2_1k.ipynb,5-60 minutes/extractor,feature dependent,Kaggle dependent,T4 dependent,per shard,rerun failed shard under same lock,cache_artifact,false,cache-v2 pass
cifar10__import__1k__none__hash__timestamp,LOCAL_CPU_IMPORT,F,P1,secure copyback validation,local,CPU,0,copied-back ZIP,hash-addressed immutable import,completed Kaggle stage,python3 -m certgen import <stage> <zip>,seconds-tens of minutes,ZIP plus extracted bytes,low,none,new immutable output only,preserve raw ZIP; follow structured repair record,cache_or_run_log_by_stage,false,integrity schema and stage validators pass
cifar10__metric-reproduction__1k__feature__hash__timestamp,LOCAL_CPU_METRIC_REPRODUCTION,G,P1,bind and cross-check exact registered metric,local,CPU,0,validated cache-v2 pair plus frozen target,immutable metric gate JSON,cache validation,python3 -m certgen sanity metric-reproduction --config <frozen.yaml> --out <new.json>,seconds-minutes,feature-cache dependent,two feature arrays plus kernels,none,immutable rerun under same hash,stop on identity or tolerance failure,sanity_artifact,false,PASS with exact target class and lineage
cifar10__sanity__1k__feature__hash__timestamp,LOCAL_CPU_SANITY,G,P1,null gap direction and protocol controls,local,CPU,0,frozen control measurements and artifact IDs,immutable sanity gate JSON,metric gate pass,python3 -m certgen sanity controls --config <frozen.yaml> --out <new.json>,seconds-minutes,artifact dependent,feature dependent,none,immutable rerun under same hash,stop at failed control; do not relax tolerance,sanity_artifact,false,all ten required controls pass
cifar10__certificate__1k__feature__hash__timestamp,LOCAL_CPU_CERTIFICATE,H,P1,first bounded-RBF nonclaim certificate,local,CPU,0,frozen study family bundle and draw plan,immutable certificate JSON,all sanity gates and family freeze,python3 -m certgen certify --study <yaml> --family <json> --features <npz> --reference-draw-plan <json> --comparison <id> --feature-space <id> --out <new.json>,seconds-minutes,feature-bundle dependent,feature dependent,none,same stream identity only,block changed stream family alpha or draw,pilot_only,false,deterministic decided censored or blocked certificate
cifar10__ranking__1k__multi__hash__timestamp,LOCAL_CPU_PARTIAL_RANKING,I,P2,certified partial graph,local,CPU,0,compatible certificate family,graph CSVs and summary JSON,certificate pilot complete,python3 -m certgen rank --family <json> --certificate-dir <dir> --out-dir <new-dir>,seconds,small,low,none,new immutable output directory,reject mixed identities; keep incomparable pairs,pilot_only,false,no forced total order and compatibility pass
cifar10__sensitivity__1k__feature__hash__timestamp,LOCAL_CPU_SENSITIVITY,I,P2,censored samples-to-decision and registered ablations,local,CPU,0,compatible certificates by frozen variant,nonclaim analysis JSON,pilot certificates,python3 -m certgen analyze samples-to-decision --certificate-dir <dir> --out <new.json>,seconds-minutes,small,low,none,new immutable output,retain censoring and exclude incompatible variants,pilot_only,false,decided censored and invalid counts retained
cifar10__figures__1k__multi__hash__timestamp,LOCAL_CPU_FIGURES,J,P3,pilot visuals or paper-gated rendering,local,CPU,0,figure request plus approved artifact IDs,planning contract or gated figure,ranking and figure approval gate,python3 -m certgen figures --request <json> --out <new.json>,seconds-minutes,small plus selected images,low,none,new immutable outputs,block unapproved lineage; do not render,planning_or_pilot,false,schema pass and explicit approval status
multibench__literature-audit__full__multi__hash__timestamp,LOCAL_CPU_LITERATURE_AUDIT,K,P3,prospective published-claim audit,local/manual,CPU,0,frozen claim registry and eligible artifacts,audited claim table,protocol frozen before curation,follow docs/experiments/CERTGEN_CVPR_LITERATURE_AUDIT_PROTOCOL.md,days of manual curation,source dependent,low,none,append-only registry,record exclusion or blocker; never invent citation,candidate_paper_evidence,false,every included claim has complete provenance
multibench__paper-gate__full__multi__hash__timestamp,LOCAL_CPU_PAPER_GATE,L,P3,explicit evidence promotion audit,local,CPU,0,complete multi-benchmark immutable lineage,paper firewall and approved artifact registry,all empirical and release gates,python3 -m certgen audit paper,minutes,small,low,none,rerun after every paper edit,remove unsupported language or block promotion,paper_evidence_candidate,false until separate future approval,firewall pass plus explicit approved artifact IDs
```

## E. Exact critical path to the first pilot

1. Place the official archive or another accepted local source under `data/sources/` without modifying it.
2. Validate: `python3 -m certgen validate reference --source <path> --explain`.
3. Materialize: `python3 -m certgen materialize reference --source <path>`; require exactly 10,000 test rows.
4. Fill and freeze the model/preflight and runtime-plan configurations; run `python3 -m certgen plan-runtime --config <frozen-runtime.yaml> --out <new-plan.json>`; then package the checkpoint-preflight input using the canonical config schema.
5. Run `notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb` on Kaggle T4x2.
6. Copy back `certgen_cvpr_checkpoint_preflight_<run_id>.zip` unchanged and record SHA-256.
7. Import: `python3 -m certgen import preflight <zip>`; require every model `PREFLIGHT_PASS`.
8. Build the 1k generation input from that exact imported preflight and the frozen seed-shard plan.
9. Run `notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb`.
10. Copy back the deterministic generation ZIP and record SHA-256.
11. Import: `python3 -m certgen import generation <zip>`; require every shard and unique ID/seed/hash.
12. Build feature input with reference draw, image manifests, extractor registry, and preprocessing locks.
13. Run `notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb` for Inception, CLIP, and the frozen DINOv2 choice.
14. Copy back the deterministic feature ZIP and record SHA-256.
15. Import: `python3 -m certgen import features <zip>`.
16. Validate every cache-v2 artifact: `python3 -m certgen validate-caches --features <npz> --sidecar <json> --artifact-root <root>`.
17. Fill and freeze `configs/cvpr/metric_reproduction_gate_template.yaml`, then run `python3 -m certgen sanity metric-reproduction --config <frozen-metric-gate.yaml> --out <new-result.json>`. The gate binds both exact sets/counts, extractor, preprocessing, metric/kernel/bandwidth, tolerance, and target provenance. With no trusted external target it emits `cross_implementation_consistency` and `not_external_reproduction`.
18. Fill and freeze `configs/cvpr/sanity_gates_template.yaml`, then run `python3 -m certgen sanity controls --config <frozen-sanity-gates.yaml> --out <new-result.json>`.
19. Require all four families: null repetition/splits, obvious-gap corruption, aggregate direction, and rejection of preprocessing/feature/bandwidth/reference-population mismatches. Stop on any failure.
20. Replace every family TBD, freeze the Bonferroni record, and hash it before inspecting certificate values.
21. Run `python3 -m certgen certify --study <frozen.yaml> --family <frozen.json> --features <bundle.npz> --reference-draw-plan <plan.json> --comparison <id> --feature-space <id> --out <certificate.json>`.
22. Build the pilot partial ranking with `python3 -m certgen rank --family <frozen-family.json> --certificate-dir <dir> --out-dir <new-dir>`; mixed features need the preregistered unanimous rule.
23. Create pilot-only figure requests; empirical paper rendering remains blocked.
24. Run `python3 -m certgen audit cvpr` and the evidence gate.
25. Stop and interpret. Do not automatically start 10k.

## F. Scale-up path

- 1k -> 10k: provenance, preflight, cache, metric, null, obvious-gap, family, and pilot interpretation gates all pass; added budget answers a registered question.
- 10k -> 50k: unresolved/censored or sensitivity questions justify cost; session/shard plan fits Kaggle limits.
- CIFAR -> benchmark 2: pilot logic and adapters survive; source/license/model pairs are verified.
- Benchmark 2 -> 3: breadth is necessary for the central conclusion.
- Image -> video: only after a strong image core and a separately valid temporal protocol.
- Pilot -> paper: immutable multi-benchmark lineage and explicit paper-approved artifact IDs; never automatic.

## G. Planning runtime tables

| Location/type | Lane | Planning range | Resource/disk rule |
|---|---|---|---|
| Local CPU | validation/import | seconds to tens of minutes | low RAM for static checks; import needs ZIP plus extracted bytes |
| Local CPU | reference materialization | minutes | source plus normalized reference view; under 1 GiB for CIFAR planning |
| Local CPU | metric/certificate/ranking | seconds-minutes | RAM can reach two or more feature arrays plus kernel work |
| Local CPU | figures | seconds-minutes | selected images plus plotting dependencies |
| Data transfer | package upload/copyback | connection-dependent; no measured estimate | record ZIP size and SHA-256 at every boundary |
| Kaggle T4x2 | checkpoint preflight | 5-30 min | model dependent; require 10 GiB free working disk |
| Kaggle T4x2 | CIFAR 1k generation, three candidates | 30 min-3 h | model/image/cache dependent |
| Kaggle T4x2 | 1k Inception | 5-30 min | feature dimension and batch dependent |
| Kaggle T4x2 | 1k CLIP | 10-45 min | feature dimension and batch dependent |
| Kaggle T4x2 | 1k DINO | 10-60 min | selected DINO revision must first be frozen |
| Kaggle T4x2 | 10k generation | 1-8 h/model | split into deterministic sessions if required |
| Kaggle T4x2 | 50k generation | potentially multiple sessions | mandatory per-session copyback checkpoints |

Transfer and ZIP sizes depend on image encoding and feature dimension. The session planner divides immutable shard IDs across sessions and mandates copyback after each complete session.

## H. Kaggle notebook instructions

Common procedure for all five notebooks: build one deterministic input ZIP with `python3 -m certgen package <preflight|generation|features> --config <frozen.yaml> --input <NAME=PATH> --out-zip <new.zip> --manifest-out <new.json>`; upload that ZIP as one private Kaggle dataset; select accelerator `GPU T4 x2`; set internet exactly as the frozen `network_allowed` policy permits; require two visible CUDA devices unless the separately approved configuration enables the logged one-T4 fallback; run every cell in order. Download the single output ZIP from the notebook output pane without modification, record SHA-256, and import locally. Before upload and after every notebook regeneration, run `python3 -m certgen audit notebooks`.

| Notebook | Required input ZIP | Internet | Resume rule | Expected output ZIP | Local import and validation | Failure recovery |
|---|---|---|---|---|---|---|
| `certgen_cvpr_checkpoint_preflight_t4x2.ipynb` | frozen preflight config, runtime adapter, model registry/cache inputs | off unless source/auth review explicitly enables it | passed model only under the same configuration and integrity hashes | `certgen_cvpr_checkpoint_preflight_<run_id>.zip` | `python3 -m certgen import preflight <zip>`; require every per-model status `PREFLIGHT_PASS` and import `passed=true` | copy back the blocked diagnostic ZIP; preserve logs; rerun failed model IDs only |
| `certgen_cvpr_cifar10_generation_t4x2_1k.ipynb` | exact imported preflight identity, frozen three-model config, two disjoint seed shards per model | frozen config only | complete image/manifest/hash shard under unchanged config | `certgen_cvpr_generation_cifar10_1k_<run_id>.zip` | `python3 -m certgen import generation <zip>`; verify unique IDs/seeds, all shards, configuration and integrity hashes | quarantine only invalid failed-shard directories; rerun exact shard IDs |
| `certgen_cvpr_generation_t4x2_generic.ipynb` | same contract for one registered benchmark/model/scale | frozen config only | identical per-shard rule | `certgen_cvpr_generation_<benchmark>_<scale>_<run_id>.zip` | same generation importer; require declared model/seed coverage | add no ad hoc adapter; return to preflight or create a new frozen config |
| `certgen_cvpr_feature_extraction_t4x2_1k.ipynb` | validated CIFAR reference/generated manifests and images, draw plan, exact Inception/CLIP/DINO registry entries, preprocessing locks, runtime adapter | off when model weights are uploaded; otherwise only by recorded source policy | finite cache plus exact sample/order/extractor/preprocessing/config hashes | `certgen_cvpr_features_cifar10_1k_<run_id>.zip` | `python3 -m certgen import features <zip>` then `python3 -m certgen validate caches --features <npz> --sidecar <json> --artifact-root <root>` for every cache | preserve blocked ZIP; rerun only failed extractor/shard identities under the same locks |
| `certgen_cvpr_feature_extraction_t4x2_generic.ipynb` | same feature contract for a registered benchmark/model/scale | frozen source policy | identical per-extractor/shard rule | `certgen_cvpr_features_<benchmark>_<scale>_<run_id>.zip` | same feature importer and cache-v2 validator; require expected roles/models/counts | stop on benchmark, feature, preprocessing, reference, dimension, or license mismatch |

The notebooks write exact output roots, per-shard status, logs, copyback instructions, integrity manifests, and a deterministic archive layout. A partial run is blocked rather than merged as success. Import preserves every raw ZIP under its content hash even when validation fails.

## I. Run dependency DAG

```text
local validation
  -> reference validate -> reference materialize
  -> preflight package -> Kaggle preflight -> copyback/import
  -> generation package -> Kaggle generation -> copyback/import
  -> feature package -> Kaggle features -> copyback/import/cache validation
  -> metric reproduction -> null controls -> obvious-gap controls
  -> frozen family -> certificate pilot -> partial ranking -> pilot figures
  -> evidence gate -> STOP/INTERPRET
  -> conditional 10k -> conditional 50k -> conditional benchmark breadth -> paper gate
```

## J. Evidence promotion

- Registry/config/runtime plans: planning artifacts.
- Preflight/environment/tiny images: run logs, never paper evidence.
- Generated images/manifests: sample/cache-adjacent artifacts, not conclusions.
- Feature arrays/sidecars: cache artifacts.
- Metric/null/obvious-gap outputs: sanity artifacts.
- First certificates/rankings: pilot artifacts, single-benchmark, non-generalized.
- Paper evidence: only after the separate immutable-lineage promotion gate.

## K. Immediate stop conditions

Stop on provenance failure, unsafe/archive/hash failure, cache schema or dimension mismatch, preprocessing/extractor/reference mismatch, preflight failure, metric reproduction failure, null calibration failure, obvious-gap direction failure, draw-plan invalidity, unfrozen family, incompatible ranking family, or paper firewall failure. Preserve raw inputs and produce one exact repair action. Do not relax the gate.

## L. Exact next action

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```

Expected output: `data/results/v9_cifar_reference_onramp.json`. Required success: `READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION`.
