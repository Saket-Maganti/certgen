#!/usr/bin/env python3
"""Build an identity-complete CIFAR 10k generation worker specification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from certgen.icml2027.common import write_json  # noqa: E402
from certgen.icml2027.execution_contract import (  # noqa: E402
    build_generation_worker_spec,
    validate_generation_job_partition,
    validate_worker_spec,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=["cifar_10k_generation"], required=True)
    parser.add_argument("--authenticated-prerequisite-set-sha256", required=True)
    parser.add_argument("--shard-size", type=int, default=500)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    seed_manifest = json.loads(
        (ROOT / "registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json").read_text(
            encoding="utf-8"
        )
    )
    contract = json.loads(
        (ROOT / "registry/icml2027/cifar_10k_v2_execution_contract_v1.json").read_text(
            encoding="utf-8"
        )
    )
    spec = build_generation_worker_spec(
        seed_manifest,
        contract,
        input_package_sha256=args.authenticated_prerequisite_set_sha256,
        shard_size=args.shard_size,
    )
    scientific = validate_worker_spec(spec, expected_lane=args.lane, contract=contract)
    partition = validate_generation_job_partition(spec["jobs"], seed_manifest)
    if not scientific["passed"] or not partition["passed"]:
        raise RuntimeError("refusing to write an invalid worker specification")
    write_json(args.out, spec)
    print(f"jobs={len(spec['jobs'])}; claim_allowed=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
