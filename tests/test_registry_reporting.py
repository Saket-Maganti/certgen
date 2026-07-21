from pathlib import Path

from certgen.cli.plan_first_pilot import write_first_pilot_plan
from certgen.cli.validate_registry import validate_registry
from certgen.gates.claim_gate import scan_text_for_forbidden_claims
from certgen.pilots.registry import read_csv_rows


def test_registry_csv_templates_parse_and_validate():
    rows = read_csv_rows("registry/candidate_model_pairs_template.csv")
    assert rows
    assert rows[0]["reported_a_score"] == "TBD"
    assert rows[0]["evidence_status"] == "non_evidence_planned"
    assert validate_registry("registry/candidate_benchmarks_template.csv", "registry/candidate_model_pairs_template.csv") == []


def test_first_pilot_plan_does_not_claim_results(tmp_path):
    out = tmp_path / "FIRST_PILOT_PLAN.md"
    markdown = write_first_pilot_plan(pairs="registry/candidate_model_pairs_template.csv", out=str(out))
    assert "No pilot run has been executed." in markdown
    assert "No decidedness fraction is available." in markdown
    assert scan_text_for_forbidden_claims(markdown, evidence_status="non_evidence_planned").passed


def test_no_results_doc_contains_required_statement():
    text = Path("docs/NO_RESULTS_YET.md").read_text(encoding="utf-8")
    assert "CertGen currently has no real empirical results, no audit number, no decidedness fraction, no ranking changes, and no paper evidence." in text


def test_command_index_includes_every_cli_command():
    text = Path("docs/COMMAND_INDEX_V1.md").read_text(encoding="utf-8")
    for command in [
        "python -m certgen.cli.validate_config",
        "python -m certgen.cli.make_smoke_artifacts",
        "python -m certgen.cli.validate_registry",
        "python -m certgen.cli.plan_first_pilot",
        "python -m certgen.cli.v1_audit",
    ]:
        assert command in text


def test_related_work_todo_has_no_fake_numeric_citations():
    text = Path("docs/RELATED_WORK_TODO.md").read_text(encoding="utf-8")
    assert "[1]" not in text


def test_reproducibility_capsule_mentions_evidence_status():
    text = Path("docs/REPRODUCIBILITY_CAPSULE_V1.md").read_text(encoding="utf-8").lower()
    assert "evidence status" in text
