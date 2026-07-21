import csv
import json

from certgen.audit.forensic_inventory import build_inventory, write_inventory


def test_inventory_is_non_evidence_and_classifies_smoke(tmp_path):
    (tmp_path / "certgen").mkdir()
    (tmp_path / "certgen" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    smoke = tmp_path / "data" / "smoke" / "v1"
    smoke.mkdir(parents=True)
    (smoke / "certificate.json").write_text(
        json.dumps({"evidence_status": "smoke_only", "claim_allowed": False}), encoding="utf-8"
    )

    rows = build_inventory(tmp_path)
    by_path = {row["path"]: row for row in rows}
    assert by_path["data/smoke/v1/certificate.json"]["evidence_class"] == "SYNTHETIC_ONLY"
    assert by_path["certgen/core.py"]["safe_to_release"] == "true"

    csv_out = tmp_path / "reports" / "inventory.csv"
    json_out = tmp_path / "reports" / "inventory.json"
    write_inventory(rows, csv_out, json_out)
    with csv_out.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 2
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["claim_allowed"] is False
    assert payload["inventory_is_empirical_evidence"] is False
