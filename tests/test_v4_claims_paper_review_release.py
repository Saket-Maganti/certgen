import csv

from certgen.literature.claim_ingest import validate_claims
from certgen.literature.claim_schema import CLAIM_FIELDS
from certgen.literature.claim_trace import build_claim_trace
from certgen.release.capsule import validate_capsule
from certgen.release.privacy_scan import scan_privacy
from certgen.reporting.figures import figure_specs
from certgen.reporting.result_cards import comparison_result_card
from certgen.reporting.tables import table_specs
from certgen.review.attacks import attack_cards


def test_v4_claim_ingest_and_trace_are_nonclaim(tmp_path):
    path = tmp_path / "claims.csv"
    row = {field: "template" for field in CLAIM_FIELDS}
    row.update(
        {
            "claim_id": "claim_1",
            "paper_title": "Template Paper",
            "citation_key": "template2026",
            "benchmark": "bench",
            "metric_name": "kid_polynomial",
            "reported_sample_size": "32",
            "claim_allowed": "false",
        }
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CLAIM_FIELDS)
        writer.writeheader()
        writer.writerow(row)

    result = validate_claims(path)
    trace = build_claim_trace(row)
    assert result["passed"]
    assert result["claim_allowed"] is False
    assert trace["claim_allowed"] is False


def test_v4_paper_specs_reviewer_cards_and_capsule_are_nonclaim():
    assert all(not figure["claim_allowed"] for figure in figure_specs())
    assert all(not table["claim_allowed"] for table in table_specs())
    assert comparison_result_card("c")["claim_allowed"] is False

    cards = attack_cards()
    assert len(cards) >= 15
    assert sum(1 for card in cards if card["blocker"]) >= 5

    capsule = validate_capsule(".")
    assert capsule["passed"]
    assert capsule["claim_allowed"] is False


def test_v4_privacy_scan_catches_private_paths_and_api_keys(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "bad.md").write_text("private path /Users/example/project\napi_key = secret\n", encoding="utf-8")
    (tmp_path / "release").mkdir()
    issues = scan_privacy(tmp_path)
    assert any("private absolute path" in issue for issue in issues)
    assert any("secret-like pattern" in issue for issue in issues)
