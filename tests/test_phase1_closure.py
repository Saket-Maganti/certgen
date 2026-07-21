from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path
from types import ModuleType

from certgen.notebooks.final_zip import validate_multipart_fallback, write_multipart_fallback
from certgen.phase1.kaggle import build_static_input, validate_input
from certgen.phase1.notebooks import validate_phase1_notebooks
from certgen.phase1.rehearsal import LABELS


def _load_report_generator() -> ModuleType:
    path = Path(__file__).parents[1] / "scripts/generate_execution_reports.py"
    spec = importlib.util.spec_from_file_location("certgen_execution_reports", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase1_notebooks_are_deterministic_and_complete() -> None:
    verdict = validate_phase1_notebooks(deterministic=True)
    assert verdict["passed"] is True
    assert [row["kind"] for row in verdict["results"]] == [
        "diagnostic",
        "preflight",
        "generation",
        "features",
    ]


def test_phase1_static_bundle_dry_run_is_deterministic() -> None:
    first = build_static_input("diagnostic", dry_run=True)
    second = build_static_input("diagnostic", dry_run=True)
    assert first["zip_sha256"] == second["zip_sha256"]
    assert first["configuration_hash"] == second["configuration_hash"]
    assert first["claim_allowed"] is False


def test_phase1_input_validator_rejects_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../escape", b"unsafe")
    verdict = validate_input(archive)
    assert verdict["passed"] is False
    assert any("unsafe ZIP member" in error for error in verdict["errors"])


def test_multipart_fallback_detects_corruption(tmp_path: Path) -> None:
    source = tmp_path / "output.zip"
    with zipfile.ZipFile(source, "w") as handle:
        handle.writestr("status.json", json.dumps({"claim_allowed": False}))
    manifest = write_multipart_fallback(source, maximum_part_bytes=16)
    assert validate_multipart_fallback(source.with_suffix(".zip.parts.json"))["passed"] is True
    (tmp_path / manifest["parts"][0]["path"]).write_bytes(b"corrupt")
    assert validate_multipart_fallback(source.with_suffix(".zip.parts.json"))["passed"] is False


def test_fixture_labels_are_complete() -> None:
    assert LABELS == {
        "synthetic_validation_only": True,
        "not_real_kaggle_input": True,
        "not_empirical_evidence": True,
        "claim_allowed": False,
    }


def test_publication_report_requires_local_and_remote_main_to_match(monkeypatch) -> None:
    generator = _load_report_generator()
    local_head = "a" * 40

    def matching_git(*args: str, check: bool = True) -> str:
        del check
        return local_head if args[0] == "rev-parse" else ""

    monkeypatch.setattr(generator, "git", matching_git)
    monkeypatch.setattr(generator.shutil, "which", lambda _: "/usr/local/bin/gh")
    matched = generator.publication_snapshot("main")
    assert matched["status"] == "GITHUB_PUSHED_AND_VERIFIED"
    assert matched["remote_verified"] is True

    def mismatching_git(*args: str, check: bool = True) -> str:
        del check
        return local_head if len(args) == 2 else "b" * 40

    monkeypatch.setattr(generator, "git", mismatching_git)
    monkeypatch.setattr(
        generator.subprocess,
        "run",
        lambda *args, **kwargs: type("Result", (), {"returncode": 0})(),
    )
    unmatched = generator.publication_snapshot("main")
    assert unmatched["status"] == "GITHUB_PUSH_FAILED"
    assert unmatched["remote_verified"] is False
