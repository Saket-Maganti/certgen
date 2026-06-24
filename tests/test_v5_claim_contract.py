from certgen.audit.claim_contract import audit_claim_contract, default_claim_contract, validate_claim_contract
from certgen.core.io import write_json


def test_v5_default_claim_contract_validates():
    contract = default_claim_contract()
    assert validate_claim_contract(contract) == []
    assert contract["claim_allowed"] is False


def test_v5_claim_contract_audit_catches_fake_claim(tmp_path):
    contract_path = tmp_path / "contract.json"
    write_json(default_claim_contract(), contract_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "paper.md").write_text("Our results demonstrate that model A is better. KID = 1.23\n", encoding="utf-8")
    result = audit_claim_contract(contract_path, roots=(str(docs),))
    assert not result["passed"]
    assert result["errors"]
