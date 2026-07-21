# CertGen Phase 1 test matrix

| Sequence | Phase | Command | Status | Exit |
|---:|---|---|---|---:|
| 1 | `baseline` | `git branch --show-current; git rev-parse HEAD; git status --short` | `PASS` | 0 |
| 2 | `discovery` | `python3 -m certgen --help` | `PASS` | 0 |
| 3 | `discovery` | `sed -n 240,900p certgen/__main__.py` | `PASS` | 0 |
| 4 | `discovery` | `sed -n 900,1120p certgen/__main__.py` | `PASS` | 0 |
| 5 | `discovery` | `rg --files notebooks/kaggle requirements artifacts/cvpr` | `FAIL` | 2 |
| 6 | `discovery` | `sed -n 1,360p certgen/notebooks/cvpr_factory.py` | `PASS` | 0 |
| 7 | `discovery` | `rg -n 'kaggle&#124;notebook&#124;T4&#124;dependency&#124;asset' tests/test_final_100_percent_pre_run.py tests/test_final_run_ready_closure.py tests/test_final_runtime_hardening.py tests/test_v7_notebook_quality.py tests/test_v6_cpu_kaggle_packaging.py tests/test_v9_execution_supercharger.py` | `PASS` | 0 |
| 8 | `discovery` | `sed -n 1,360p scripts/build_cvpr_preexecution_assets.py` | `PASS` | 0 |
| 9 | `discovery` | `python3 -m certgen readiness --help` | `PASS` | 0 |
| 10 | `discovery` | `python3 -m certgen next-action --help` | `PASS` | 0 |
| 11 | `discovery` | `python3 -m certgen doctor --help` | `PASS` | 0 |
| 12 | `discovery` | `python3 -m certgen kaggle --help` | `EXPECTED_BOUNDARY` | 2 |
| 13 | `discovery` | `python3 -m certgen notebooks --help` | `EXPECTED_BOUNDARY` | 2 |
| 14 | `discovery` | `python3 -m certgen audit --help` | `PASS` | 0 |
| 15 | `discovery` | `sed -n 1,360p certgen/cvpr/package.py` | `PASS` | 0 |
| 16 | `discovery` | `sed -n 1,360p certgen/notebooks/cvpr_static_analyzer.py` | `PASS` | 0 |
| 17 | `discovery` | `sed -n 1,360p certgen/notebooks/environment_bootstrap.py` | `PASS` | 0 |
| 18 | `discovery` | `sed -n 1,360p certgen/notebooks/final_zip.py` | `PASS` | 0 |
| 19 | `discovery` | `sed -n 1,360p certgen/max_ceiling/contracts.py` | `PASS` | 0 |
| 20 | `discovery` | `sed -n 1,360p certgen/audit/final_pre_run_audit.py` | `PASS` | 0 |
| 21 | `discovery` | `sed -n 1,360p certgen/max_ceiling/audit.py` | `PASS` | 0 |
| 22 | `baseline_checks` | `python3 -m compileall -q certgen scripts tests` | `PASS` | 0 |
| 23 | `baseline_checks` | `python3 -c 'import certgen; import certgen.__main__; import certgen.cvpr; import certgen.notebooks.cvpr_factory; print("imports_ok")'` | `PASS` | 0 |
| 24 | `baseline_checks` | `python3 -m pytest -q` | `PASS` | 0 |
| 25 | `discovery` | `sed -n 1,340p certgen/notebooks/cvpr_static_analyzer.py` | `PASS` | 0 |
| 26 | `discovery` | `sed -n 1,420p certgen/cvpr/prepare.py` | `PASS` | 0 |
| 27 | `discovery` | `rg -n 'license:&#124;redistribution_allowed&#124;public_archive_included&#124;private_mount&#124;required&#124;expected_preprocessing&#124;model_id:&#124;feature_space_id:' registry/cvpr/model_registry.yaml registry/cvpr/feature_space_registry.yaml configs/cvpr/profiles/cifar_integrity_minimal.yaml` | `PASS` | 0 |
| 28 | `discovery` | `sed -n 1,240p configs/cvpr/profiles/cifar_integrity_minimal.yaml` | `PASS` | 0 |
| 29 | `discovery` | `sed -n 170,230p tests/test_final_runtime_hardening.py` | `PASS` | 0 |
| 30 | `discovery` | `rg -n 'write_canonical_notebooks&#124;NOTEBOOK_SPECS&#124;analyze_all' tests` | `PASS` | 0 |
| 31 | `discovery` | `sed -n 1,420p certgen/notebooks/environment_bootstrap.py` | `PASS` | 0 |
| 32 | `discovery` | `rg -n 'def run_builder_faithful_synthetic&#124;stages\[&#124;stages\.append&#124;rehearsal_status&#124;def rehearse_failures&#124;cases =' certgen/cvpr/builder_faithful.py certgen/max_ceiling/contracts.py` | `PASS` | 0 |
| 33 | `discovery` | `sed -n 378,590p certgen/cvpr/builder_faithful.py` | `PASS` | 0 |
| 34 | `discovery` | `sed -n 477,650p certgen/max_ceiling/contracts.py` | `PASS` | 0 |
| 35 | `discovery` | `rg -n 'FAILURE_CASES&#124;zero_gpu&#124;one_gpu&#124;zip_traversal&#124;missing_seed&#124;duplicate_seed&#124;partial_zip&#124;asset' certgen/max_ceiling/contracts.py` | `PASS` | 0 |
| 36 | `discovery` | `sed -n 410,480p certgen/max_ceiling/contracts.py` | `PASS` | 0 |
| 37 | `discovery` | `rg -n 'def load_frozen_configuration&#124;def verify_input_integrity&#124;def copyback_instructions' certgen/notebooks/kaggle_io.py` | `PASS` | 0 |
| 38 | `discovery` | `sed -n 1,300p certgen/notebooks/subprocess_orchestrator.py` | `PASS` | 0 |
| 39 | `discovery` | `sed -n 1,220p certgen/notebooks/worker_contract.py` | `PASS` | 0 |
| 40 | `discovery` | `sed -n 1,300p certgen/notebooks/final_zip.py` | `PASS` | 0 |
| 41 | `implementation_check` | `python3 -m compileall -q certgen/notebooks/worker_contract.py certgen/notebooks/workers/diagnostic_worker.py certgen/notebooks/final_zip.py` | `PASS` | 0 |
| 42 | `implementation_check` | `sed -n 24,72p certgen/notebooks/worker_contract.py` | `PASS` | 0 |
| 43 | `implementation_check` | `rg -n diagnostic certgen/notebooks/worker_contract.py` | `PASS` | 0 |
| 44 | `implementation_check` | `sed -n 126,148p certgen/notebooks/worker_contract.py` | `PASS` | 0 |
| 45 | `discovery` | `sed -n 45,95p tests/test_final_runtime_hardening.py` | `PASS` | 0 |
| 46 | `discovery` | `sed -n 1,300p certgen/notebooks/workers/preflight_worker.py` | `PASS` | 0 |
| 47 | `discovery` | `rg -n 'class AssetPolicy&#124;class NetworkMode' certgen/notebooks/model_assets.py certgen/notebooks/network_policy.py` | `PASS` | 0 |
| 48 | `discovery` | `sed -n 1,24p certgen/notebooks/model_assets.py` | `PASS` | 0 |
| 49 | `implementation_check` | `python3 -m compileall -q certgen/phase1 certgen/__main__.py certgen/notebooks` | `PASS` | 0 |
| 50 | `notebooks` | `python3 -m certgen notebooks generate --explain --json` | `PASS` | 0 |
| 51 | `notebooks` | `python3 -m certgen notebooks check-determinism --explain --json` | `FAIL` | 2 |
| 52 | `notebooks` | `python3 -m certgen notebooks generate --json` | `PASS` | 0 |
| 53 | `notebooks` | `python3 -m certgen notebooks check-determinism --json` | `PASS` | 0 |
| 54 | `implementation_check` | `rg -n 'def assert_cpu_only' certgen/notebooks/cvpr_runtime.py` | `FAIL` | 1 |
| 55 | `implementation_check` | `sed -n 1,160p certgen/notebooks/cvpr_runtime.py` | `PASS` | 0 |
| 56 | `implementation_check` | `python3 -m compileall -q certgen/phase1 certgen/__main__.py scripts/run_all_available_cpu_stages.py` | `PASS` | 0 |
| 57 | `cpu_orchestrator` | `python3 scripts/run_all_available_cpu_stages.py --dry-run --explain` | `EXPECTED_BOUNDARY` | 10 |
| 58 | `fixture_rehearsal` | `python3 -c 'import json; from certgen.phase1.rehearsal import run_phase1_rehearsal; print(json.dumps(run_phase1_rehearsal(), indent=2, sort_keys=True))'` | `PASS` | 0 |
| 59 | `regression` | `python3 -m pytest -q tests/test_cvpr_architecture.py tests/test_final_runtime_hardening.py tests/test_final_run_ready_closure.py` | `PASS` | 0 |
| 60 | `cli_surface` | `python3 -m certgen kaggle --help` | `PASS` | 0 |
| 61 | `cli_surface` | `python3 -m certgen notebooks --help` | `PASS` | 0 |
| 62 | `cli_surface` | `python3 -m certgen audit --help` | `PASS` | 0 |
| 63 | `cli_surface` | `python3 -m certgen kaggle build-input --help` | `PASS` | 0 |
| 64 | `test_discovery` | `rg --files tests` | `PASS` | 0 |
| 65 | `phase1_tests` | `python3 -m pytest -q tests/test_phase1_closure.py` | `PASS` | 0 |
| 66 | `final_default_pytest` | `python3 -m pytest -q` | `PASS` | 0 |
| 67 | `integration_audit` | `python3 -m pytest -q -m integration_audit` | `PASS` | 0 |
| 68 | `statistical_tests` | `python3 -m pytest -q tests/test_cvpr_statistical_contract.py tests/test_confidence_sequences.py tests/test_mmd_streams.py tests/test_optional_stopping_lab.py` | `PASS` | 0 |
| 69 | `artifact_contract_tests` | `python3 -m pytest -q tests/test_schemas.py tests/test_feature_cache_v2_contract.py tests/test_engineering_evidence_safety.py` | `PASS` | 0 |
| 70 | `runtime_hardening_tests` | `python3 -m pytest -q tests/test_final_runtime_hardening.py` | `PASS` | 0 |
| 71 | `real_execution_closure_tests` | `python3 -m pytest -q tests/test_real_execution_closure.py` | `PASS` | 0 |
| 72 | `final_readiness_tests` | `python3 -m pytest -q tests/test_final_100_percent_pre_run.py tests/test_final_run_ready_closure.py` | `PASS` | 0 |
| 73 | `post_cache_tests` | `python3 -m pytest -q tests/test_post_cache_final_closure.py` | `PASS` | 0 |
| 74 | `maximum_ceiling_tests` | `python3 -m pytest -q tests/test_maximum_ceiling.py` | `PASS` | 0 |
| 75 | `kaggle_bundle_tests` | `python3 -m pytest -q tests/test_v6_cpu_kaggle_packaging.py tests/test_phase1_closure.py` | `PASS` | 0 |
| 76 | `notebook_tests` | `python3 -m pytest -q tests/test_v7_notebook_quality.py tests/test_cvpr_architecture.py` | `PASS` | 0 |
| 77 | `provenance_tests` | `python3 -m pytest -q tests/test_provenance_ledger.py tests/test_reference_draw_plan.py` | `PASS` | 0 |
| 78 | `replay_tests` | `python3 -m pytest -q tests/test_replay_and_pilot_report_v3.py` | `PASS` | 0 |
| 79 | `claim_evidence_tests` | `python3 -m pytest -q tests/test_claim_gate.py tests/test_v5_claim_contract.py tests/test_evidence_status.py` | `PASS` | 0 |
| 80 | `release_tests` | `python3 -m pytest -q tests/test_archive_portable.py tests/test_v5_paper_proof_release.py tests/test_v4_claims_paper_review_release.py` | `PASS` | 0 |
| 81 | `post_cache_repair_tests` | `python3 -m pytest -q tests/test_v7_importers.py tests/test_feature_cache_v3.py` | `PASS` | 0 |
| 82 | `final_readiness_forensic_tests` | `python3 -m pytest -q tests/test_forensic_final_audit.py tests/test_forensic_inventory.py` | `PASS` | 0 |
| 83 | `kaggle_provenance_tests` | `python3 -m pytest -q tests/test_v9_execution_supercharger.py tests/test_v7_runledger.py` | `PASS` | 0 |
| 84 | `ruff` | `python3 -m ruff check certgen scripts tests` | `FAIL` | 1 |
| 85 | `ruff` | `python3 -m ruff check certgen scripts tests` | `PASS` | 0 |
| 86 | `mypy_discovery` | `rg -n 'mypy.*error&#124;Full mypy&#124;mypy debt&#124;Found [0-9]+ errors' reports CERTGEN_CVPR_100_PERCENT_PRE_RUN_EXECUTION_HANDBOOK.md CERTGEN_CVPR_100_PERCENT_PRE_RUN_READINESS_REPORT.md CERTGEN_CVPR_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md CERTGEN_CVPR_FINAL_EXECUTION_HANDBOOK.md CERTGEN_CVPR_FINAL_RUNTIME_HARDENING_REPORT.md CERTGEN_CVPR_FINAL_RUN_READY_CLOSURE_REPORT.md CERTGEN_CVPR_FINAL_RUN_READY_EXECUTION_HANDBOOK.md CERTGEN_CVPR_MAX_PREEXECUTION_BUILD_REPORT.md CERTGEN_CVPR_REAL_EXECUTION_CLOSURE_REPORT.md CERTGEN_CVPR_RUN_READY_EXECUTION_HANDBOOK.md CERTGEN_FORENSIC_AUDIT_AND_MAXIMUM_CEILING_REPORT.md CERTGEN_MAX_CEILING_EXECUTION_HANDBOOK.md CERTGEN_MAX_CEILING_PRE_RUN_READINESS_REPORT.md CERTGEN_MAX_CEILING_SINGLE_FILE_HANDOFF.md CERTGEN_POST_CACHE_FINAL_FIX_REPORT.md docs` | `PASS` | 0 |
| 87 | `critical_mypy` | `python3 -m mypy --no-incremental certgen/phase1 scripts/run_all_available_cpu_stages.py scripts/phase1_command_runner.py certgen/notebooks/workers/diagnostic_worker.py` | `FAIL` | 1 |
| 88 | `critical_mypy` | `python3 -m mypy --no-incremental --follow-imports=skip certgen/phase1 scripts/run_all_available_cpu_stages.py scripts/phase1_command_runner.py certgen/notebooks/workers/diagnostic_worker.py` | `PASS` | 0 |
| 89 | `full_mypy_debt` | `python3 -m mypy --no-incremental certgen` | `EXPECTED_BOUNDARY` | 1 |
| 90 | `audit_discovery` | `rg -n 'privacy&#124;restricted.asset&#124;release scan&#124;paper compilation&#124;latexmk&#124;pdflatex&#124;paper firewall&#124;final.pre.run&#124;maximum.ceiling' README.md Makefile pyproject.toml scripts commands reports/CERTGEN_FINAL_HARDENING_COMMAND_LEDGER.csv reports/CERTGEN_FINAL_100_PERCENT_COMMAND_LEDGER.csv` | `FAIL` | 2 |
| 91 | `audit_discovery` | `sed -n 1,260p certgen/release/privacy_scan.py` | `PASS` | 0 |
| 92 | `paper_firewall` | `python3 -m certgen audit paper --explain --json` | `PASS` | 0 |
| 93 | `privacy_scan` | `python3 -c 'from certgen.release.privacy_scan import scan_privacy; issues=scan_privacy(); print(issues); raise SystemExit(bool(issues))'` | `PASS` | 0 |
| 94 | `restricted_asset_scan` | `python3 -c 'from pathlib import Path; suffixes={".pt",".pth",".bin",".safetensors",".ckpt",".onnx"}; roots=[Path("artifacts/cvpr/kaggle_inputs"),Path("release"),Path("dist")]; hits=[str(p) for r in roots if r.exists() for p in r.rglob("*") if p.is_file() and p.suffix.lower() in suffixes]; print(hits); raise SystemExit(bool(hits))'` | `PASS` | 0 |
| 95 | `release_scan` | `python3 -m certgen.audit.release_safety_v5 --out /tmp/certgen_phase1_release_safety.md --json-out /tmp/certgen_phase1_release_safety.json` | `PASS` | 0 |
| 96 | `paper_compile` | `mkdir -p /tmp/certgen_phase1_paper` | `PASS` | 0 |
| 97 | `paper_compile` | `pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/certgen_phase1_paper main.tex` | `PASS` | 0 |
| 98 | `paper_compile` | `pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/certgen_phase1_paper main.tex` | `PASS` | 0 |
| 99 | `cpu_autorun` | `python3 scripts/run_all_available_cpu_stages.py --resume --explain` | `EXPECTED_BOUNDARY` | 10 |
| 100 | `kaggle_inventory` | `python3 -m certgen kaggle inventory --explain --json` | `PASS` | 0 |
| 101 | `kaggle_build_diagnostic` | `python3 -m certgen kaggle build-input --stage diagnostic --explain --json` | `PASS` | 0 |
| 102 | `kaggle_build_preflight` | `python3 -m certgen kaggle build-input --stage preflight --profile cifar_integrity_minimal --explain --json` | `PASS` | 0 |
| 103 | `kaggle_build_generation` | `python3 -m certgen kaggle build-input --stage generation --scale 1k --study artifacts/cvpr/study/cifar_integrity_minimal.yaml --explain --json` | `PASS` | 0 |
| 104 | `kaggle_build_features` | `python3 -m certgen kaggle build-input --stage features --scale 1k --study artifacts/cvpr/study/cifar_integrity_minimal.yaml --explain --json` | `PASS` | 0 |
| 105 | `kaggle_validate_input` | `python3 -m certgen kaggle validate-input artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip --explain --json` | `PASS` | 0 |
| 106 | `kaggle_inspect_input` | `python3 -m certgen kaggle inspect-input artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip --explain --json` | `PASS` | 0 |
| 107 | `kaggle_next` | `python3 -m certgen kaggle next --explain --json` | `PASS` | 0 |
| 108 | `reporting` | `python3 -c 'import json; from certgen.phase1.reporting import generate_phase1_reports; print(json.dumps(generate_phase1_reports(), indent=2, sort_keys=True))'` | `PASS` | 0 |
| 109 | `kaggle_launch_audit` | `python3 -m certgen audit kaggle-launch --explain --json` | `PASS` | 0 |
| 110 | `cpu_execution_audit` | `python3 -m certgen audit cpu-execution --explain --json` | `PASS` | 0 |
| 111 | `final_pre_run_audit` | `python3 -m certgen audit final-pre-run --explain --json` | `PASS` | 0 |
| 112 | `maximum_ceiling_audit` | `python3 -m certgen audit maximum-ceiling --explain --json` | `PASS` | 0 |
| 113 | `cvpr_audit` | `python3 -m certgen audit cvpr --explain --json` | `PASS` | 0 |
| 114 | `final_state_readiness` | `python3 -m certgen readiness --explain --json` | `PASS` | 0 |
| 115 | `final_state_next_action` | `python3 -m certgen next-action --explain` | `PASS` | 0 |
| 116 | `final_state_doctor` | `python3 -m certgen doctor --json` | `PASS` | 0 |
| 117 | `final_state_kaggle_next` | `python3 -m certgen kaggle next --explain` | `PASS` | 0 |
| 118 | `final_compileall` | `python3 -m compileall -q certgen scripts tests` | `PASS` | 0 |
| 119 | `final_imports` | `python3 -c 'import certgen; import certgen.__main__; import certgen.phase1.audit; import certgen.phase1.kaggle; import certgen.phase1.notebooks; import certgen.phase1.reporting; print("imports_ok")'` | `PASS` | 0 |
| 120 | `final_phase1_tests` | `python3 -m pytest -q tests/test_phase1_closure.py` | `PASS` | 0 |
| 121 | `final_notebook_determinism` | `python3 -m certgen notebooks check-determinism --json` | `PASS` | 0 |
| 122 | `final_ruff` | `python3 -m ruff check certgen scripts tests` | `PASS` | 0 |
| 123 | `final_diff_check` | `git diff --check` | `PASS` | 0 |
| 124 | `final_reporting` | `python3 -c 'import json; from certgen.phase1.reporting import generate_phase1_reports; print(json.dumps(generate_phase1_reports(), indent=2, sort_keys=True))'` | `PASS` | 0 |
| 125 | `final_artifact_seal` | `python3 -c 'import json; from pathlib import Path; from certgen.phase1.kaggle import BUNDLES, inspect_input, source_code_hash; required=["CERTGEN_PHASE1_PRE_GPU_COMPLETION_REPORT.md","CERTGEN_KAGGLE_T4X2_EXECUTION_HANDBOOK.md","CERTGEN_KAGGLE_RUN_LAUNCHBOARD.md","CERTGEN_KAGGLE_INPUT_BUNDLE_CATALOG.md","CERTGEN_KAGGLE_DEPENDENCY_AND_ASSET_GUIDE.md","CERTGEN_PHASE1_NEXT_ACTION.md","reports/CERTGEN_PHASE1_BASELINE.md","reports/CERTGEN_PHASE1_COMMAND_LEDGER.csv","reports/CERTGEN_PHASE1_CURRENT_STATE.json","reports/CERTGEN_PHASE1_TEST_MATRIX.md","reports/CERTGEN_PHASE1_ARTIFACT_INVENTORY.csv","reports/CERTGEN_KAGGLE_RUNTIME_ESTIMATES.csv","reports/CERTGEN_KAGGLE_RUNTIME_ASSUMPTIONS.md","reports/CERTGEN_KAGGLE_FINAL_LAUNCH_AUDIT.md"]; missing=[p for p in required if not Path(p).is_file()]; current=source_code_hash(); bundles={stage:inspect_input(path) for stage,path in BUNDLES.items()}; stale={stage:row["source_code_hash"] for stage,row in bundles.items() if row["source_code_hash"]!=current}; state=json.loads(Path("reports/CERTGEN_PHASE1_CURRENT_STATE.json").read_text()); print(json.dumps({"missing":missing,"stale_bundles":stale,"bundles":{k:{"passed":v["passed"],"sha256":v["zip_sha256"]} for k,v in bundles.items()},"phase1_status":state["phase1_status"],"cifar_present":Path("data/sources/cifar-10-python.tar.gz").is_file(),"claim_allowed":state["claim_allowed"]},indent=2,sort_keys=True)); raise SystemExit(bool(missing or stale or not all(v["passed"] for v in bundles.values())))'` | `PASS` | 0 |
| 126 | `orchestrator_ruff` | `python3 -m ruff check scripts/run_all_available_cpu_stages.py` | `PASS` | 0 |
| 127 | `orchestrator_capability` | `python3 scripts/run_all_available_cpu_stages.py --dry-run --explain` | `EXPECTED_BOUNDARY` | 10 |
| 128 | `orchestrator_resume_seal` | `python3 scripts/run_all_available_cpu_stages.py --resume --explain` | `EXPECTED_BOUNDARY` | 10 |
| 129 | `report_seal` | `python3 -c 'import json; from certgen.phase1.reporting import generate_phase1_reports; print(json.dumps(generate_phase1_reports(), indent=2, sort_keys=True))'` | `PASS` | 0 |
