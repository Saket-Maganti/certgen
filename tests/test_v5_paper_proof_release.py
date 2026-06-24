from certgen.audit.paper_scaffold_audit import audit_paper_scaffold
from certgen.audit.proof_obligation_audit import audit_proof_obligations
from certgen.audit.release_safety_v5 import scan_release_safety_v5


def test_v5_paper_and_proof_scaffolds_pass():
    assert audit_paper_scaffold()["passed"]
    proof = audit_proof_obligations()
    assert proof["passed"]
    assert proof["obligations"] >= 10


def test_v5_release_safety_catches_fixture_leaks(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "bad.md").write_text("/Users/example/project\napi_key = secret\n", encoding="utf-8")
    (tmp_path / "paper").mkdir()
    (tmp_path / "release").mkdir()
    (tmp_path / "commands").mkdir()
    result = scan_release_safety_v5(tmp_path)
    assert not result["passed"]
    assert any("private local path" in issue for issue in result["issues"])
    assert any("secret-like token" in issue for issue in result["issues"])
