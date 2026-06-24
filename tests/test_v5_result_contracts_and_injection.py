from certgen.audit.analysis_plan_audit import write_analysis_plan_lock
from certgen.audit.result_contract_audit import audit_result_contracts
from certgen.core.io import write_json
from certgen.paper.result_injection import default_result_card, inject_results, validate_placeholder_artifact
from certgen.reporting.result_contracts import default_result_contracts, validate_result_contracts


def test_v5_result_contracts_pass_on_repo():
    result = audit_result_contracts()
    assert result["passed"]
    assert result["contracts"] >= 9


def test_v5_result_contract_validation_rejects_fake_numbers():
    card = default_result_card()
    card["samples_to_decision"] = 123
    errors = validate_placeholder_artifact(card)
    assert errors
    assert validate_result_contracts(default_result_contracts()) == []


def test_v5_placeholder_result_injection_and_hash_mismatch(tmp_path):
    plan_path = tmp_path / "plan.json"
    hash_path = tmp_path / "hash.txt"
    write_analysis_plan_lock(plan_path, hash_path)

    card_path = tmp_path / "card.json"
    trace_path = tmp_path / "trace.json"
    write_json(default_result_card(), card_path)
    write_json(
        {
            "claim_id": "c",
            "paper_location": "paper/sections/05_results_placeholder.tex",
            "result_artifact_id": "card",
            "source_provenance_id": "p",
            "feature_cache_id": "f",
            "preprocessing_lock_id": "l",
            "metric_reproduction_id": "m",
            "certificate_id": "cert",
            "audit_id": "audit",
            "evidence_status": "template_only",
            "claim_allowed": False,
        },
        trace_path,
    )
    result = inject_results(card_path, trace_path, plan_path, hash_path, tmp_path / "out")
    assert result["errors"] == []
    assert result["placeholder_retained"]
    hash_path.write_text("wrong\n", encoding="utf-8")
    blocked = inject_results(card_path, trace_path, plan_path, hash_path, tmp_path / "out2")
    assert "analysis-plan hash mismatch" in blocked["errors"]
