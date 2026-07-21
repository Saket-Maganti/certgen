# CertGen Forensic Repository Coherence Audit

This is a repository-integrity audit, not empirical model evidence.

Passed: `True`
Checks: `8/8`
Project status: `LOCAL_RESEARCH_CORE_VALID_BLOCKED_BY_REFERENCE_INPUT`
Claim allowed: `false`

| Check | Passed | Detail |
|---|---:|---|
| `required_consolidated_artifacts_exist` | `True` | all present |
| `no_machine_readable_claim_allowed_true` | `True` | none |
| `current_state_is_valid_json` | `True` | reports/CERTGEN_CURRENT_STATE.json |
| `one_recognized_top_level_status` | `True` | LOCAL_RESEARCH_CORE_VALID_BLOCKED_BY_REFERENCE_INPUT |
| `current_state_blocks_empirical_claims` | `True` | False |
| `singular_executable_next_action` | `True` | {'action': 'VALIDATE_USER_SUPPLIED_CIFAR10_ARCHIVE', 'user_input_path': 'data/sources/cifar-10-python.tar.gz', 'exact_command': 'python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain', 'expected_artifact': 'data/results/v9_cifar_reference_onramp.json', 'success_status': 'READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION'} |
| `metric_capability_boundary_is_conservative` | `True` | passed |
| `claim_evidence_ledger_has_no_promoted_claim` | `True` | passed |
