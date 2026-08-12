#!/usr/bin/env python3
"""Freeze the live final-closure baseline and immutable legacy hashes."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from certgen.icml2027.common import file_sha256, load_mapping, write_json  # noqa: E402


OUT = ROOT / "reports/icml2027/final_closure"
STARTING_COMMIT = "3506826ceb7fda0b46b514f43f17e38b6e62aac3"
LEGACY_FILES = {
    "diagnostic_notebook": "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb",
    "diagnostic_input_zip": "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip",
    "preflight_notebook": "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
    "preflight_input_zip": "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip",
    "legacy_1k_generation_notebook": "notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb",
    "legacy_1k_feature_notebook": "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb",
    "legacy_frozen_profile": "artifacts/cvpr/study/cifar_integrity_minimal.yaml",
    "legacy_reference_draw_plan": "registry/manifests/cvpr/reference_draw_plan.json",
    "legacy_pilot_link": "registry/icml2027/legacy_pilot_link.yaml",
    "cifar_10k_v1_config": "configs/icml2027/cifar_confirmatory_10k_v1.yaml",
}


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    local_head = _git("rev-parse", "HEAD")
    remote_head = _git("rev-parse", "origin/main")
    if local_head != STARTING_COMMIT or remote_head != STARTING_COMMIT:
        raise RuntimeError("final-closure baseline must start from the declared pushed checkpoint")
    hashes = {name: file_sha256(ROOT / path) for name, path in LEGACY_FILES.items()}
    v2_config = ROOT / "configs/icml2027/cifar_confirmatory_10k_v2.yaml"
    v2 = load_mapping(v2_config)
    reference_plan = ROOT / str(v2["reference_draw"]["plan_path"])
    payload = {
        "schema_version": "certgen.icml2027.final_closure_baseline.v1",
        "starting_commit": local_head,
        "origin_main": remote_head,
        "branch": _git("branch", "--show-current"),
        "legacy_hashes": hashes,
        "cifar_10k_v2_config_sha256": file_sha256(v2_config),
        "cifar_10k_v2_study_id": v2["study_id"],
        "reference_plan_semantic_sha256": v2["reference_draw"]["plan_sha256"],
        "reference_plan_file_sha256": file_sha256(reference_plan),
        "python": sys.version,
        "platform": platform.platform(),
        "claim_allowed": False,
    }
    write_json(OUT / "CERTGEN_FINAL_CLOSURE_BASELINE.json", payload)
    lines = [
        "# CertGen ICML 2027 final-closure baseline",
        "",
        f"- Starting/local/origin commit: `{local_head}`",
        f"- Branch: `{payload['branch']}`",
        "- Initial worktree: four pre-existing untracked prompt-pack Markdown files; preserved",
        f"- Python: `{sys.version.split()[0]}`; platform: `{platform.platform()}`",
        f"- CIFAR 10k v2 config SHA-256: `{payload['cifar_10k_v2_config_sha256']}`",
        f"- Reference-plan semantic SHA-256: `{payload['reference_plan_semantic_sha256']}`",
        f"- Reference-plan file SHA-256: `{payload['reference_plan_file_sha256']}`",
        "",
        "## Immutable legacy hashes",
        "",
    ]
    for name, path in LEGACY_FILES.items():
        lines.append(f"- `{name}` — `{path}` — `{hashes[name]}`")
    lines.extend(
        [
            "",
            "Live compile/import, test, integration, security, bundle, provenance, replay, release, Ruff, and mypy results are recorded in the paired command ledger. `claim_allowed=false`.",
            "",
        ]
    )
    (OUT / "CERTGEN_FINAL_CLOSURE_BASELINE.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
