#!/usr/bin/env python3
"""Freeze the v1 execution contract and exact 20k generator-seed manifest."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from certgen.icml2027.common import _atomic_write, canonical_json_bytes, write_json  # noqa: E402
from certgen.icml2027.execution_contract import (  # noqa: E402
    build_execution_contract,
    build_generator_seed_manifest,
    seed_collision_audit,
    validate_generator_seed_manifest,
)


def main() -> int:
    manifest = build_generator_seed_manifest()
    validation = validate_generator_seed_manifest(manifest)
    collision = seed_collision_audit()
    if not validation["passed"] or not collision["passed"]:
        raise RuntimeError("generator seed freeze failed")
    contract = build_execution_contract(manifest, root=ROOT)
    _atomic_write(
        ROOT / "registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json",
        canonical_json_bytes(manifest),
    )
    write_json(
        ROOT / "registry/icml2027/cifar_10k_v2_execution_contract_v1.json",
        contract,
    )
    write_json(
        ROOT / "reports/icml2027/final_closure/GENERATOR_SEED_COLLISION_AUDIT.json",
        collision,
    )
    print(f"seed_manifest_sha256={manifest['manifest_sha256']}")
    print(f"execution_contract_sha256={contract['execution_contract_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
