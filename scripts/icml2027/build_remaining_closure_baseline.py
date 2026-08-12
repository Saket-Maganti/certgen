#!/usr/bin/env python3
"""Freeze the live remaining-closure baseline and immutable identities."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from certgen.icml2027.common import file_sha256, load_mapping, stable_hash, write_json  # noqa: E402


OUT = ROOT / "reports/icml2027/remaining_closure"
STARTING_COMMIT = "77460dfe6ee1ae8ea294e6a2c36a98cb88e152b3"
IDENTITY_FILES = {
    "diagnostic_notebook": "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb",
    "diagnostic_input_zip": "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip",
    "preflight_notebook": "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
    "preflight_input_zip": "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip",
    "legacy_1k_generation_notebook": "notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb",
    "legacy_1k_feature_notebook": "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb",
    "legacy_frozen_profile": "artifacts/cvpr/study/cifar_integrity_minimal.yaml",
    "legacy_reference_draw_plan": "registry/manifests/cvpr/reference_draw_plan.json",
    "legacy_pilot_link": "registry/icml2027/legacy_pilot_link.yaml",
    "cifar_10k_v2_config": "configs/icml2027/cifar_confirmatory_10k_v2.yaml",
    "cifar_10k_v2_reference_draw_plan": "registry/manifests/icml2027/cifar10_reference_draw_plan_10k_v2.json",
    "cifar_10k_v2_seed_manifest": "registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json",
    "cifar_10k_v2_execution_contract": "registry/icml2027/cifar_10k_v2_execution_contract_v1.json",
}


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    local_head = _git("rev-parse", "HEAD")
    remote_head = _git("rev-parse", "origin/main")
    if local_head != STARTING_COMMIT or remote_head != STARTING_COMMIT:
        raise RuntimeError("remaining-closure baseline must start from the declared pushed checkpoint")
    hashes = {name: file_sha256(ROOT / path) for name, path in IDENTITY_FILES.items()}
    config = load_mapping(ROOT / IDENTITY_FILES["cifar_10k_v2_config"])
    legacy = load_mapping(ROOT / IDENTITY_FILES["legacy_frozen_profile"])
    semantic = {
        "study_id": config["study_id"],
        "study_status": config["status"],
        "seed_plan": config["seed_plan"],
        "comparison_family": {
            "models": config["models"],
            "feature_spaces": config["feature_spaces"],
            "multiplicity": config["multiplicity"],
            "alpha": config["alpha"],
        },
        "reference_draw": config["reference_draw"],
        "legacy_profile_id": legacy["profile_id"],
        "legacy_configuration_hash": legacy["configuration_hash"],
    }
    payload = {
        "schema_version": "certgen.icml2027.remaining_closure_baseline.v1",
        "starting_commit": local_head,
        "origin_main": remote_head,
        "branch": _git("branch", "--show-current"),
        "identity_hashes": hashes,
        "semantic_identity": semantic,
        "semantic_identity_sha256": stable_hash(semantic),
        "python": sys.version,
        "platform": platform.platform(),
        "initial_worktree": _git("status", "--short").splitlines(),
        "claim_allowed": False,
    }
    write_json(OUT / "CERTGEN_REMAINING_CLOSURE_BASELINE.json", payload)
    lines = [
        "# CertGen ICML 2027 remaining-closure baseline",
        "",
        f"- Starting/local/origin commit: `{local_head}`",
        f"- Branch: `{payload['branch']}`",
        f"- Python/platform: `{sys.version.split()[0]}` / `{platform.platform()}`",
        f"- Semantic identity SHA-256: `{payload['semantic_identity_sha256']}`",
        "- Initial worktree: four pre-existing untracked prompt-pack Markdown files plus the two baseline-ledger helpers used to record this live reproduction; all prompt packs are preserved.",
        "",
        "## Frozen file identities",
        "",
    ]
    for name, path in IDENTITY_FILES.items():
        lines.append(f"- `{name}` — `{path}` — `{hashes[name]}`")
    lines.extend(
        [
            "",
            "The paired command ledger records live compile/import, test, integration, bundle, provenance, replay, privacy, secrets, restricted-asset, Ruff, mypy, release, and diff checks. `claim_allowed=false`.",
            "",
        ]
    )
    (OUT / "CERTGEN_REMAINING_CLOSURE_BASELINE.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
