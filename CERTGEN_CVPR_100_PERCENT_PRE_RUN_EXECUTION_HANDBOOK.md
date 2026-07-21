# CertGen CVPR 100% Pre-Run Execution Handbook

> **Superseded by `CERTGEN_CVPR_RUN_READY_EXECUTION_HANDBOOK.md`.** Retained as a historical pre-run snapshot; do not use its reference-path instructions for a new run.

Every step below has `claim_permission: false`; paper promotion remains a separate gate.

## 1. Place the official CIFAR archive

Command: `install -m 0444 <official-cifar-archive> data/sources/cifar-10-python.tar.gz`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: user-supplied official archive. Output: `data/sources/cifar-10-python.tar.gz`. Runtime class: seconds. Resume: reuse only the same verified bytes. Failure recovery: correct the source; do not download or substitute. Evidence class: prerequisite only. Claim permission: false. Completion test: the file exists and is read-only.

## 2. Validate reference

Command: `python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: official archive. Output: `data/results/v9_cifar_reference_onramp.json`. Runtime class: seconds. Resume: rerun safely. Failure recovery: replace only with an accepted official layout. Evidence class: validation only. Claim permission: false. Completion test: status is `READY_FOR_REFERENCE_MATERIALIZATION`.

## 3. Materialize reference

Command: `python3 -m certgen materialize reference --source data/sources/cifar-10-python.tar.gz`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: validated archive. Output: `registry/manifests/cvpr/cifar10_reference.jsonl`. Runtime class: minutes. Resume: identical immutable manifest only. Failure recovery: quarantine partial output and repeat. Evidence class: input artifact. Claim permission: false. Completion test: 10,000 decoded, unique, hash-bound rows.

## 4. Select pilot profile

Command: `python3 -m certgen profiles show cifar_integrity_minimal`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: versioned profile. Output: printed profile and hash. Runtime class: seconds. Resume: same profile hash. Failure recovery: fix profile validation before proceeding. Evidence class: planning. Claim permission: false. Completion test: profile validates with no placeholder.

## 5. Freeze study

Command: `python3 -m certgen freeze study --profile cifar_integrity_minimal --out artifacts/cvpr/study/cifar_integrity_minimal.yaml`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: selected profile and registries. Output: immutable study YAML. Runtime class: seconds. Resume: never overwrite; reuse exact hash or create a new version. Failure recovery: repair prospective registry inputs. Evidence class: preregistration. Claim permission: false. Completion test: frozen-study validator passes.

## 6. Prepare reference draw

Command: `python3 -m certgen prepare reference-draw --profile cifar_integrity_minimal --study artifacts/cvpr/study/cifar_integrity_minimal.yaml --reference-manifest registry/manifests/cvpr/cifar10_reference.jsonl`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: frozen study and reference population. Output: registered `reference_draw_plan.json`. Runtime class: seconds. Resume: identical configuration only. Failure recovery: create a new study for any changed choice. Evidence class: input protocol. Claim permission: false. Completion test: canonical draw validation passes.

## 7. Prepare preflight package

Command: `python3 -m certgen prepare preflight --profile cifar_integrity_minimal --asset-policy ONLINE_PREFLIGHT_DOWNLOAD`. Location: local. CPU_or_GPU: CPU. Network policy: package creation none; policy is frozen for Kaggle. Input: profile and registries. Output: preflight input ZIP/config. Runtime class: seconds-minutes. Resume: identical configuration only. Failure recovery: resolve license/adapter blockers. Evidence class: planning. Claim permission: false. Completion test: package status is ready.

## 8. Validate preflight input

Command: `python3 -m certgen validate kaggle-input artifacts/cvpr/preflight/certgen_cvpr_preflight_input.zip`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: preflight ZIP. Output: structural verdict. Runtime class: seconds. Resume: rerun. Failure recovery: rebuild from immutable inputs. Evidence class: validation only. Claim permission: false. Completion test: verdict passes.

## 9. Run real model/extractor preflight

Command: run `notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb`. Location: Kaggle T4x2. CPU_or_GPU: GPU. Network policy: exactly the frozen asset policy; dependencies and assets are separate. Input: validated preflight ZIP. Output: canonical preflight output ZIP. Runtime class: minutes. Resume: compatible completion markers and identical hashes only. Failure recovery: restart only failed workers or rebuild changed configuration. Evidence class: run log. Claim permission: false. Completion test: every expected worker and integrity file passes.

## 10. Validate and import preflight output

Command: `python3 -m certgen validate kaggle-output <preflight-output.zip> --kind preflight && python3 -m certgen import preflight <preflight-output.zip> --out-json data/results/cvpr/preflight_import_status.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: copied-back ZIP. Output: registered immutable import. Runtime class: seconds-minutes. Resume: identical ZIP only. Failure recovery: retain original ZIP and repair importer blockers. Evidence class: run log. Claim permission: false. Completion test: import status passes.

## 11. Ingest runtime calibration

Command: `python3 -m certgen runtime-plan ingest-preflight <preflight-runtime-report.json> --config configs/cvpr/runtime_plan_template.yaml --out artifacts/cvpr/runtime/runtime_plan.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: real preflight timing/memory report. Output: runtime plan. Runtime class: seconds. Resume: same report hash. Failure recovery: rerun preflight rather than invent measurements. Evidence class: planning from run log. Claim permission: false. Completion test: every selected lane has measured calibration.

## 12. Prepare generation package

Command: `python3 -m certgen prepare generation --scale 1k --study artifacts/cvpr/study/cifar_integrity_minimal.yaml`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: imported preflight, reference, study. Output: generation ZIP/config. Runtime class: seconds-minutes. Resume: identical configuration only. Failure recovery: fix the failing upstream hash. Evidence class: planning. Claim permission: false. Completion test: generation package is ready.

## 13. Validate generation input

Command: `python3 -m certgen validate kaggle-input artifacts/cvpr/generation/certgen_cvpr_generation_1k_input.zip`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: generation ZIP. Output: structural verdict. Runtime class: seconds. Resume: rerun. Failure recovery: rebuild package. Evidence class: validation. Claim permission: false. Completion test: verdict passes.

## 14. Run 1k generation

Command: run `notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb`. Location: Kaggle T4x2. CPU_or_GPU: GPU. Network policy: dependencies allowed as frozen; model assets offline after preflight. Input: validated generation ZIP. Output: canonical generation output ZIP. Runtime class: measured GPU session. Resume: same worker identity/config/input/assets only. Failure recovery: retry failed shard with OOM backoff. Evidence class: pilot artifact. Claim permission: false. Completion test: all expected seeds and image manifests pass.

## 15. Validate and import generation output

Command: `python3 -m certgen validate kaggle-output <generation-output.zip> --kind generation && python3 -m certgen import generation <generation-output.zip> --out-json data/results/cvpr/generation_import_status.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: copied-back ZIP. Output: registered import. Runtime class: minutes. Resume: identical ZIP. Failure recovery: retain and diagnose without modifying output. Evidence class: pilot artifact. Claim permission: false. Completion test: import passes.

## 16. Prepare controls

Command: `python3 -m certgen prepare controls --study artifacts/cvpr/study/cifar_integrity_minimal.yaml --reference-draw-plan registry/manifests/cvpr/reference_draw_plan.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: frozen study/draw/reference. Output: registered control package. Runtime class: seconds-minutes. Resume: identical configuration only. Failure recovery: fix source integrity, never tune severity. Evidence class: input artifact. Claim permission: false. Completion test: null disjointness, obvious-gap pairing, and integrity pass.

## 17. Prepare feature package

Command: `python3 -m certgen prepare features --controls-dir artifacts/cvpr/controls/<study-hash>`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: generation import, materialized draw images, controls, preflight assets. Output: feature ZIP/config. Runtime class: minutes. Resume: identical configuration only. Failure recovery: repair missing role/source. Evidence class: planning. Claim permission: false. Completion test: expected model/reference/control roles are complete.

## 18. Validate feature input

Command: `python3 -m certgen validate kaggle-input artifacts/cvpr/features/certgen_cvpr_features_input.zip`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: feature ZIP. Output: structural/decode verdict. Runtime class: seconds-minutes. Resume: rerun. Failure recovery: rebuild from source artifacts. Evidence class: validation. Claim permission: false. Completion test: every image path resolves and decodes.

## 19. Run feature extraction

Command: run `notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb`. Location: Kaggle T4x2. CPU_or_GPU: GPU. Network policy: offline validated model caches; frozen dependency policy. Input: validated feature ZIP/private CLIP cache. Output: canonical feature output ZIP. Runtime class: measured GPU session. Resume: exact worker/config/schema/input/asset identity only. Failure recovery: restart failed role shard. Evidence class: cache artifact. Claim permission: false. Completion test: all role/extractor shards pass.

## 20. Validate and import feature output

Command: `python3 -m certgen validate kaggle-output <feature-output.zip> --kind feature && python3 -m certgen import features <feature-output.zip> --out-json data/results/cvpr/feature_import_status.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: copied-back ZIP. Output: registered import. Runtime class: minutes. Resume: identical ZIP. Failure recovery: preserve ZIP and repair validation issue. Evidence class: cache artifact. Claim permission: false. Completion test: import passes.

## 21. Merge features

Command: use the exact command emitted by `python3 -m certgen next-action`, of the form `python3 -m certgen merge features --run <registered-run-id>`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: registered feature shards. Output: cache-v2 role groups. Runtime class: minutes. Resume: immutable output directory only. Failure recovery: quarantine failed partial merge. Evidence class: cache artifact. Claim permission: false. Completion test: merge manifest and every cache validate.

## 22. Validate cache-v2

Command: use `certgen next-action` so `--features`, `--sidecar`, and `--artifact-root` are verified registered paths. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: registered cache group. Output: cache validation status. Runtime class: seconds-minutes. Resume: rerun. Failure recovery: repair/re-extract the affected role only. Evidence class: cache validation. Claim permission: false. Completion test: all family-required roles pass.

## 23. Freeze family

Command: `python3 -m certgen prepare family --study artifacts/cvpr/study/cifar_integrity_minimal.yaml`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: study/comparison registry. Output: `artifacts/cvpr/family/family.json`. Runtime class: seconds. Resume: exact family hash. Failure recovery: a changed family requires a new study. Evidence class: multiplicity protocol. Claim permission: false. Completion test: family validator passes.

## 24. Prepare certificate inputs

Command: run the exact artifact-resolved `python3 -m certgen prepare certificate-inputs ...` emitted by `certgen next-action`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: frozen family/study/draw and registered cache roles. Output: one immutable bundle per hypothesis. Runtime class: seconds-minutes. Resume: identical bundle configuration only. Failure recovery: repair missing cache role; never add post-hoc members. Evidence class: pilot input. Claim permission: false. Completion test: bundle manifest covers the family exactly.

## 25. Validate family operational completeness

Command: `python3 -m certgen validate certificate-inputs --study <registered-study> --family <registered-family> --inputs-root artifacts/cvpr/certificate_inputs && python3 -m certgen validate family-operational --study <registered-study> --family <registered-family> --inputs-root artifacts/cvpr/certificate_inputs`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: immutable bundles. Output: input and family operational statuses. Runtime class: seconds. Resume: rerun. Failure recovery: repair the named member only. Evidence class: validation. Claim permission: false. Completion test: `FAMILY_OPERATIONALLY_READY`.

## 26. Run metric reproduction

Command: `python3 -m certgen sanity metric-reproduction --config <frozen-gate-config> --out data/results/cvpr/metric_reproduction.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: validated registered caches. Output: reproduction gate. Runtime class: seconds-minutes. Resume: identical hashes. Failure recovery: stop and repair implementation/contract. Evidence class: sanity artifact. Claim permission: false. Completion test: status `PASS`.

## 27. Run sanity gates

Command: `python3 -m certgen sanity controls --config <frozen-gate-config> --out data/results/cvpr/sanity_controls.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: null/obvious-gap bundles and reproduction pass. Output: control gate. Runtime class: seconds-minutes. Resume: identical inputs. Failure recovery: `REPAIR`; do not tune controls. Evidence class: sanity artifact. Claim permission: false. Completion test: expected null and direction gates pass.

## 28. Run certificates

Command: run each artifact-resolved `certgen certify` command for every operational family bundle. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: registered bundle/study/family/draw. Output: registered certificate and lineage card. Runtime class: seconds-minutes per hypothesis. Resume: identical stream identity only; replay is not an independent test. Failure recovery: mark affected member invalid/blocked. Evidence class: pilot only. Claim permission: false. Completion test: family certificate coverage is complete.

## 29. Build partial ranking

Command: run the exact artifact-resolved `certgen rank` command from `certgen next-action`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: registered family certificates. Output: provenance-bearing ranking graph. Runtime class: seconds. Resume: rebuild only into a new absent directory. Failure recovery: fix incompatible certificate inputs. Evidence class: pilot analysis. Claim permission: false. Completion test: no missing unexcluded family comparisons.

## 30. Run cross-feature analysis

Command: `python3 -m certgen analyze cross-feature --certificate-dir <registered-certificate-dir> --out data/results/cvpr/cross_feature_analysis.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: registered multi-feature certificates. Output: agreement/disagreement report. Runtime class: seconds. Resume: identical certificates. Failure recovery: preserve disagreements; never force consensus. Evidence class: pilot analysis. Claim permission: false. Completion test: every comparison has a policy category.

## 31. Generate pilot stop/go report

Command: `python3 -m certgen analyze pilot-stop-go --pilot-summary <complete-pilot-summary.json> --out data/results/cvpr/pilot_stop_go.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: complete fixed gate statuses. Output: STOP/REPAIR/SCALE decision and eligible expansions. Runtime class: seconds. Resume: identical summary. Failure recovery: fill missing real gates; do not infer. Evidence class: decision support. Claim permission: false. Completion test: protocol returns a supported decision.

## 32. Stop and interpret

Command: `python3 -m certgen audit cvpr`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: ranking, cross-feature, and stop/go artifacts. Output: final nonclaim audit. Runtime class: seconds-minutes. Resume: rerun. Failure recovery: return to the first failing registered gate. Evidence class: audit only. Claim permission: false. Completion test: interpretation is recorded before any scale-up or new study version.

At the current pre-run boundary, the singular command is:

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```
