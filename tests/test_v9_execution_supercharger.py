import json
import hashlib
import zipfile
from pathlib import Path

import yaml

from certgen.audit.v9_execution_supercharger_audit import REQUIRED_PATHS, _has_claim_allowed_true, run_audit
from certgen.data.cifar_reference_super_onramp import run_onramp
from certgen.notebooks.v9_static_analyzer import NOTEBOOKS, run_analysis
from certgen.packaging.v9_import_repair import import_repair
from certgen.paper.v9_paper_firewall import run_firewall
from certgen.pipeline.v9_next_action import ACTIONS, determine_next_action
from certgen.pipeline.v9_runtime_budget_planner import build_plan
from certgen.core.hashing import stable_hash_json


def test_v9_cifar_super_onramp_detects_fake_official_archive(tmp_path):
    root = tmp_path / "cifar_root" / "cifar-10-batches-py"
    root.mkdir(parents=True)
    for name in [*(f"data_batch_{idx}" for idx in range(1, 6)), "test_batch"]:
        (root / name).write_bytes(b"fixture-only")

    payload = run_onramp(
        search_roots=[str(tmp_path / "cifar_root")],
        out_json=tmp_path / "onramp.json",
        out_report=tmp_path / "onramp.md",
        explain=True,
    )

    assert payload["status_code"] == "READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION"
    assert payload["materialization_can_proceed"] is True
    assert payload["claim_allowed"] is False
    assert payload["detected_paths"][0]["layout"] == "official_cifar_10_batches_py"


def test_v9_cifar_super_onramp_blocks_missing_reference(tmp_path):
    payload = run_onramp(
        search_roots=[str(tmp_path / "empty")],
        out_json=tmp_path / "onramp.json",
        out_report=tmp_path / "onramp.md",
    )

    assert payload["status_code"] == "BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE"
    assert payload["materialization_can_proceed"] is False
    assert payload["claim_allowed"] is False


def test_v9_exact_next_action_from_clean_tmp_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    action = determine_next_action()

    assert action["action"] == "PROVIDE_CIFAR_REFERENCE"
    assert action["action"] in ACTIONS
    assert action["evidence_allowed"] is False
    assert action["blocker"] == "BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE"


def test_v9_exact_next_action_after_onramp_detection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results = tmp_path / "data" / "results"
    results.mkdir(parents=True)
    (results / "v9_cifar_reference_onramp.json").write_text(
        json.dumps(
            {
                "materialization_can_proceed": True,
                "detected_paths": [{"path": "/user_provided_local_path_redacted/cifar", "layout": "official"}],
                "exact_next_command": "CIFAR_ROOT=/user_provided_local_path_redacted/cifar commands/v6_cpu_execution/01_materialize_reference_from_local_root.sh",
                "claim_allowed": False,
            }
        )
    )

    action = determine_next_action()

    assert action["action"] == "MATERIALIZE_CIFAR_REFERENCE"
    assert action["location"] == "CPU"
    assert action["evidence_allowed"] is False


def test_v9_import_repair_accepts_fake_preflight_zip(tmp_path):
    zip_path = tmp_path / "certgen_checkpoint_preflight_outputs.zip"
    config = {
        "kind": "preflight",
        "run_id": "fixture-preflight-import",
        "claim_allowed": False,
    }
    config["configuration_hash"] = stable_hash_json(config)
    status_text = json.dumps(
            {
                "status_code": "PREFLIGHT_PASS",
                "output_schema_version": "certgen.cvpr.preflight_output.v2",
                "expected_workers": ["model_preflight", "extractor_preflight"],
                "completed_workers": ["model_preflight", "extractor_preflight"],
                "configuration_hash": config["configuration_hash"],
            "results": [
                {
                    "checkpoint_id": checkpoint,
                    "checkpoint_revision": revision,
                    "status_code": "PREFLIGHT_PASS",
                    "claim_allowed": False,
                }
                for checkpoint, revision in [
                    ("google/ddpm-cifar10-32", "267b167dc01f0e4e61923ea244e8b988f84deb80"),
                    ("FrankCCCCC/ddpm_ema_cifar10", "6aa387f240fbb00d0e003f93a3b994f56dd98dc2"),
                    ("FrankCCCCC/cfm-cifar10-32", "b3f30358497e11ce5011c00614c9b0521262f51c"),
                ]
                ],
                "extractor_results": [
                    {
                        "extractor_id": "fixture_extractor",
                        "status_code": "EXTRACTOR_PREFLIGHT_PASS",
                        "claim_allowed": False,
                    }
                ],
            "evidence_status": "run_log_only",
            "claim_allowed": False,
        }
    )
    log_text = "run_log_only\nnot paper evidence\n"
    files = {
        "configuration.yaml": yaml.safe_dump(config, sort_keys=False),
        "run_identity.json": json.dumps(
            {
                "run_id": config["run_id"],
                "configuration_hash": config["configuration_hash"],
                "input_manifest_hash": "i" * 64,
                "asset_manifest_hash": "a" * 64,
                "claim_allowed": False,
            }
        ),
        "checkpoint_preflight_status.json": status_text,
        "per_model/model_preflight/status.json": json.dumps(
            {"status_code": "PREFLIGHT_PASS", "claim_allowed": False}
        ),
        "per_extractor/extractor_preflight/status.json": json.dumps(
            {"status_code": "EXTRACTOR_PREFLIGHT_PASS", "claim_allowed": False}
        ),
        "logs/preflight.log": log_text,
    }
    with zipfile.ZipFile(zip_path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr(
            "integrity_manifest.json",
            json.dumps(
                {
                    "files": [
                        {
                            "path": name,
                            "size": len(data.encode()),
                            "sha256": hashlib.sha256(data.encode()).hexdigest(),
                        }
                        for name, data in files.items()
                    ],
                    "claim_allowed": False,
                }
            ),
        )

    payload = import_repair(
        kind="preflight",
        zip_path=zip_path,
        out_dir=tmp_path / "imported",
        out_json=tmp_path / "import.json",
        out_report=tmp_path / "import.md",
        registry_path=tmp_path / "artifact_registry.jsonl",
    )

    assert payload["passed"] is True
    assert payload["status_code"] == "IMPORT_REPAIR_READY"
    assert payload["claim_allowed"] is False
    assert (tmp_path / "imported" / "_raw_zip" / zip_path.name).exists()


def test_v9_import_repair_blocks_unknown_zip_member(tmp_path):
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("unexpected.bin", b"bad")
        archive.writestr("checkpoint_preflight_status.json", json.dumps({"claim_allowed": False}))

    payload = import_repair(
        kind="preflight",
        zip_path=zip_path,
        out_dir=tmp_path / "imported",
        out_json=tmp_path / "import.json",
        out_report=tmp_path / "import.md",
    )

    assert payload["passed"] is False
    assert any("unknown file refused" in error for error in payload["errors"])


def test_v9_notebook_static_analyzer_passes_repo_notebooks():
    payload = run_analysis()

    assert payload["passed"] is True
    assert {item["path"] for item in payload["results"]} == set(NOTEBOOKS)
    assert payload["claim_allowed"] is False


def test_v9_runtime_budget_planner_all_scales(tmp_path):
    for scale in ["1k", "10k", "50k"]:
        payload = build_plan(scale, out_json=tmp_path / f"{scale}.json", out_report=tmp_path / f"{scale}.md")
        assert payload["scale"] == scale
        assert payload["label"] == "planning estimates only, not empirical project results"
        assert payload["claim_allowed"] is False
        assert "generation" in payload["planning_estimates"]


def test_v9_paper_firewall_blocks_unsafe_tmp_paper(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "main.tex").write_text("pilot-only proves a main empirical result\n")

    payload = run_firewall(out_json=tmp_path / "firewall.json", out_report=tmp_path / "firewall.md")

    assert payload["passed"] is False
    assert payload["blockers"]
    assert payload["claim_allowed"] is False


def test_v9_paper_firewall_passes_safe_tmp_placeholder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "main.tex").write_text("NO_REAL_EVIDENCE\nTBD_REAL_RUN_REQUIRED\n")

    payload = run_firewall(out_json=tmp_path / "firewall.json", out_report=tmp_path / "firewall.md")

    assert payload["passed"] is True
    assert payload["claim_allowed"] is False


def test_v9_audit_required_paths_exist():
    missing = [path for path in REQUIRED_PATHS.values() if not Path(path).exists()]

    assert missing == []


def test_v9_final_audit_smoke_passes_without_real_execution(tmp_path):
    payload = run_audit(tmp_path / "audit.md", tmp_path / "audit.json")

    assert payload["passed"] is True
    assert payload["status_code"] == "V9_SUPERCHARGER_READY_BLOCKED_BY_INPUTS"
    assert payload["claim_allowed"] is False
    assert payload["next_action"]["evidence_allowed"] is False


def test_v9_semantic_claim_allowed_true_detector():
    assert _has_claim_allowed_true({"claim_allowed": False}) is False
    assert _has_claim_allowed_true({"nested": [{"claim_allowed": True}]}) is True


def test_v9_no_forbidden_metric_or_fid_claim_strings():
    v9_paths = [
        *Path("certgen").rglob("v9_*.py"),
        *Path("commands/v9_cpu_execution").glob("*.sh"),
        *Path("notebooks/kaggle").glob("v9_*.ipynb"),
        *Path("docs").glob("V9_*.md"),
    ]
    guard_sources = {"v9_paper_firewall.py"}
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in v9_paths
        if path.exists() and path.name not in guard_sources
    )

    forbidden = [
        "fabricated metric",
        "fake metric",
        "final undecided fraction is",
        "we find that reported wins",
        "fid certificate",
        "fid certified",
    ]
    assert [item for item in forbidden if item in text] == []
