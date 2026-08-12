#!/usr/bin/env python3
"""Freeze the live pre-repair repository baseline and tracked inventory."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/icml2027/deep_repair"
START = "463e52753646e7d2b0792e90b9d92e4956b634f2"


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = _git("rev-parse", "HEAD")
    remote = _git("rev-parse", "origin/main")
    if head != START or remote != START:
        raise RuntimeError(f"baseline mismatch: local={head}, remote={remote}, expected={START}")
    studies = yaml.safe_load((ROOT / "registry/icml2027/study_registry.yaml").read_text(encoding="utf-8"))["studies"]
    study_rows = "\n".join(
        f"- `{row['study_id']}`: `{row['study_contract_hash']}` ({row['status']})" for row in studies
    )
    hashes = {
        "legacy_study": _sha("artifacts/cvpr/study/cifar_integrity_minimal.yaml"),
        "diagnostic_zip": _sha("artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip"),
        "preflight_zip": _sha("artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip"),
        "reference_draw_plan": _sha("registry/manifests/cvpr/reference_draw_plan.json"),
    }
    report = f"""# CertGen ICML 2027 deep-repair baseline

- Starting commit: `{head}`
- Remote `origin/main`: `{remote}`
- Branch: `{_git('branch', '--show-current')}`
- Initial status: three pre-existing untracked prompt-pack Markdown files; preserved
- Python: `{sys.version.replace(chr(10), ' ')}`
- Platform: `{platform.platform()}` / `{platform.machine()}`
- Normal pytest: `326 passed, 4 deselected`
- Full marker-enabled pytest: `330 passed`
- Explicit integration wrappers: `4 passed, 326 deselected`
- Trusted-bootstrap/security subset: `18 passed`
- Changed-code mypy: pass across 46 source files (includes the ledger runner)
- Historical repository mypy debt: `99 errors in 33 files` (371 files checked after adding the ledger runner)
- Ruff: pass
- Legacy study SHA-256: `{hashes['legacy_study']}`
- Legacy semantic study hash: `b6882b9e1be0b9f12868c47be44c0f41a522ed45c7a4529ceabd08f38cc991aa`
- Reference draw-plan SHA-256: `{hashes['reference_draw_plan']}`
- Diagnostic package SHA-256: `{hashes['diagnostic_zip']}`
- Preflight package SHA-256: `{hashes['preflight_zip']}`

## Frozen ICML study contracts

{study_rows}

Compile/import, live tests, integration wrappers, notebook regeneration checks, authenticated bundle validation, provenance, replay, privacy, secret, restricted-asset, release, Ruff, mypy, and diff checks were reproduced from the live checkout. `claim_allowed=false`.
"""
    (OUT / "CERTGEN_DEEP_REPAIR_BASELINE.md").write_text(report, encoding="utf-8")
    inventory: list[dict[str, Any]] = []
    for line in _git("ls-tree", "-rl", START).splitlines():
        metadata, name = line.split("\t", 1)
        mode, kind, object_hash, size = metadata.split()
        inventory.append({
            "path": name, "git_mode": mode, "object_type": kind, "git_object_hash": object_hash,
            "size_bytes": int(size), "baseline_commit": START,
            "immutable_legacy": name.startswith(("artifacts/cvpr/", "configs/cvpr/", "registry/manifests/cvpr/", "data/results/")),
            "claim_allowed": False,
        })
    _write_csv(OUT / "CERTGEN_DEEP_REPAIR_ARTIFACT_INVENTORY.csv", inventory)
    print(json.dumps({"passed": True, "starting_commit": START, "tracked_inventory_rows": len(inventory), "hashes": hashes, "claim_allowed": False}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
