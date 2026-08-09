"""Automated source/license and execution go/no-go gates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.icml2027.common import load_mapping, write_csv, write_json


REQUIRED_GATES = (
    "source_verified",
    "license_reviewed",
    "revision_pinned",
    "adapter_validated",
    "reference_protocol_frozen",
    "feature_protocol_frozen",
    "compute_feasible",
    "released_sample_semantics_clear",
)


def audit_go_no_go(registry_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    registry = load_mapping(registry_path)
    records = registry.get("records", registry.get("models", registry.get("benchmarks", [])))
    rows: list[dict[str, Any]] = []
    for record in records:
        gates = record.get("gates", {})
        failed = [gate for gate in REQUIRED_GATES if gates.get(gate) is not True]
        rows.append(
            {
                "record_id": record.get("model_id") or record.get("benchmark_id") or record.get("record_id"),
                "status": "GO" if not failed else "NO_GO",
                "failed_gates": ";".join(failed),
                "blocker": "" if not failed else record.get("blocker", "execution gates incomplete"),
                "human_action": "" if not failed else record.get("human_action", "verify and freeze missing gates"),
                "planning_only": True,
                "claim_allowed": False,
            }
        )
    target = Path(out_path)
    write_csv(target, rows)
    payload = {
        "schema_version": "certgen.icml2027.go_no_go_audit.v1",
        "records": len(rows),
        "go": sum(row["status"] == "GO" for row in rows),
        "no_go": sum(row["status"] == "NO_GO" for row in rows),
        "passed": True,
        "planning_only": True,
        "claim_allowed": False,
    }
    write_json(target.with_suffix(".json"), payload)
    return payload
