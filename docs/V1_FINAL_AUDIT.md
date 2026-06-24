# CertGen V1 Final Audit

Audit status: `passed`

| Check | Status | Detail |
|---|---:|---|
| `package_imports` | `pass` | certgen 0.1.0 |
| `smoke_config_validates` | `pass` | configs/certgen_v1_smoke.yaml validates |
| `schemas_serialize` | `pass` | DatasetRecord serializes to JSON dict |
| `evidence_statuses_enforced` | `pass` | real_evidence_candidate is blocked in smoke mode |
| `claim_gate_catches_forbidden_phrases` | `pass` | forbidden claim language: we find that, model a beats model b |
| `fid_policy_blocks_clean_cs` | `pass` | FID-like metrics cannot enter the clean CS path in V1 |
| `smoke_metrics_run` | `pass` | kid=0.124864; fid_identical=0.000000 |
| `clean_core_certificate_runs` | `pass` | status=certified_a_better |
| `reports_pass_claim_gate` | `pass` | claim gate passed |
| `no_results_doc_exists` | `pass` | docs/NO_RESULTS_YET.md |
| `registry_templates_exist` | `pass` | registry/candidate_benchmarks_template.csv, registry/candidate_model_pairs_template.csv, registry/audit_claims_template.csv |
| `no_generated_artifact_marked_real_status` | `pass` | no generated JSON artifact uses real_evidence_candidate |
| `docs_do_not_claim_audit_findings` | `pass` | selected docs are claim-safe |
| `command_index_exists` | `pass` | command index includes V1 commands |
| `pytest_passes` | `pass` | 33 passed in 0.21s |
