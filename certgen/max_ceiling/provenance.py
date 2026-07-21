"""Content-addressed execution provenance DAG."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from certgen.core.hashing import stable_hash_json
from certgen.max_ceiling.common import (
    artifact_root,
    load_study,
    sha256_file,
    study_hash,
    write_json_idempotent,
    write_text_idempotent,
)
from certgen.packaging.artifact_registry import NONRETAINED_VALIDATION_STATUSES


STAGE_ORDER = (
    "reference",
    "study_freeze",
    "reference_draw",
    "preflight_package",
    "preflight_result",
    "generation_package",
    "generation_result",
    "controls",
    "feature_package",
    "feature_result",
    "cache_v2",
    "metric_gates",
    "sanity_gates",
    "family",
    "certificate_inputs",
    "certificates",
    "ranking",
    "cross_feature_analysis",
    "pilot_decision",
)


def _registry_rows(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid artifact registry JSON at line {number}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"artifact registry line {number} is not an object")
        rows.append(payload)
    return rows


def _parent_ids(row: Mapping[str, Any]) -> list[str]:
    raw = row.get("parent_artifact_ids", row.get("parent_artifacts", []))
    if not isinstance(raw, list):
        raise ValueError(f"artifact {row.get('artifact_id')} parent list is invalid")
    return [str(item.get("artifact_id")) if isinstance(item, Mapping) else str(item) for item in raw]


def _parent_hashes(row: Mapping[str, Any]) -> dict[str, str]:
    raw = row.get("parent_artifact_ids", row.get("parent_artifacts", []))
    return {
        str(item.get("artifact_id")): str(item.get("content_hash"))
        for item in raw
        if isinstance(item, Mapping) and item.get("artifact_id") and item.get("content_hash")
    }


def _row_hash(row: Mapping[str, Any]) -> str:
    digest = row.get("content_hash")
    if not digest and isinstance(row.get("hash"), Mapping):
        digest = row["hash"].get("value")
    return str(digest or "")


def _node_from_row(row: Mapping[str, Any], selected_study_hash: str) -> dict[str, Any]:
    path = str(row.get("path", ""))
    return {
        "artifact_id": str(row.get("artifact_id", "")),
        "artifact_type": str(row.get("artifact_type", "")),
        "schema_version": str(row.get("schema_version", "")),
        "content_hash": _row_hash(row),
        "configuration_hash": str(row.get("configuration_hash", "")),
        "study_hash": str(row.get("study_hash", selected_study_hash)),
        "parent_artifact_ids": _parent_ids(row),
        "source_paths": list(map(str, row.get("source_paths", [path]) or [path])),
        "created_at": str(row.get("created_at", "unknown")),
        "evidence_class": str(row.get("evidence_class", "unknown")),
        "claim_allowed": row.get("claim_allowed"),
        "validation_status": str(row.get("validation_status", "unknown")),
        "stage": str(row.get("stage", row.get("artifact_type", "unknown"))),
        "_declared_parent_hashes": _parent_hashes(row),
    }


def build_provenance_graph(
    study_path: str | Path,
    *,
    registry_path: str | Path = "data/artifact_registry.jsonl",
    root: str | Path = ".",
    write: bool = True,
    out_json: str | Path | None = None,
    out_dot: str | Path | None = None,
) -> dict[str, Any]:
    study = load_study(study_path)
    selected_hash = study_hash(study)
    study_id = f"study:{selected_hash}"
    nodes: list[dict[str, Any]] = [
        {
            "artifact_id": study_id,
            "artifact_type": "study_freeze",
            "schema_version": "certgen.maximum_ceiling.provenance_node.v1",
            "content_hash": sha256_file(study_path),
            "configuration_hash": selected_hash,
            "study_hash": selected_hash,
            "parent_artifact_ids": [],
            "source_paths": [str(Path(study_path))],
            "created_at": "frozen_study_artifact",
            "evidence_class": str(study.get("evidence_class", "prospective_protocol")),
            "claim_allowed": False,
            "validation_status": "FROZEN_VALID",
            "stage": "study_freeze",
            "_declared_parent_hashes": {},
        }
    ]
    registry_rows = _registry_rows(registry_path)
    latest_by_path_and_type = {
        (str(row.get("path", "")), str(row.get("artifact_type", ""))): index
        for index, row in enumerate(registry_rows)
        if str(row.get("path", "")) and not row.get("study_hash")
    }
    study_bound_paths_and_types = {
        (str(row.get("path", "")), str(row.get("artifact_type", "")))
        for row in registry_rows
        if row.get("study_hash") == selected_hash and str(row.get("path", ""))
    }
    for index, row in enumerate(registry_rows):
        if row.get("validation_status") in NONRETAINED_VALIDATION_STATUSES:
            continue
        row_path = str(row.get("path", ""))
        row_key = (row_path, str(row.get("artifact_type", "")))
        if not row.get("study_hash") and row_key in study_bound_paths_and_types:
            continue
        if (
            row_path
            and not row.get("study_hash")
            and latest_by_path_and_type.get(row_key) != index
        ):
            continue
        row_study = row.get("study_hash")
        if row_study not in {None, "", selected_hash}:
            continue
        node = _node_from_row(row, selected_hash)
        if node["artifact_id"] == study_id:
            raise ValueError("artifact registry collides with the frozen-study node")
        nodes.append(node)
    nodes.sort(key=lambda item: str(item["artifact_id"]))
    edges: list[dict[str, Any]] = [
        {
            "parent_artifact_id": parent,
            "child_artifact_id": node["artifact_id"],
            "dependency_reason": f"{node['stage']} consumes immutable parent {parent}",
            "declared_parent_content_hash": node["_declared_parent_hashes"].get(parent),
        }
        for node in nodes
        for parent in node["parent_artifact_ids"]
    ]
    clean_nodes = [{key: value for key, value in node.items() if not key.startswith("_")} for node in nodes]
    payload: dict[str, Any] = {
        "schema_version": "certgen.maximum_ceiling.provenance_dag.v1",
        "study_hash": selected_hash,
        "stage_order": list(STAGE_ORDER),
        "nodes": clean_nodes,
        "edges": sorted(edges, key=lambda item: (item["parent_artifact_id"], item["child_artifact_id"])),
        "evidence_class": "lineage_metadata_only",
        "claim_allowed": False,
    }
    payload["graph_hash"] = stable_hash_json(payload)
    if write:
        output_root = artifact_root(study, root) / "provenance"
        json_path = Path(out_json) if out_json else output_root / "provenance_graph.json"
        dot_path = Path(out_dot) if out_dot else output_root / "provenance_graph.dot"
        write_json_idempotent(payload, json_path)
        write_text_idempotent(to_dot(payload), dot_path)
        payload["json_path"] = str(json_path)
        payload["dot_path"] = str(dot_path)
    return payload


def _cycle(nodes: Iterable[str], edges: Iterable[Mapping[str, Any]]) -> list[str] | None:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edges:
        adjacency.setdefault(str(edge["parent_artifact_id"]), []).append(str(edge["child_artifact_id"]))
    active: set[str] = set()
    done: set[str] = set()

    def visit(node: str, trail: list[str]) -> list[str] | None:
        if node in active:
            return trail[trail.index(node) :] + [node]
        if node in done:
            return None
        active.add(node)
        for child in adjacency.get(node, []):
            found = visit(child, [*trail, child])
            if found:
                return found
        active.remove(node)
        done.add(node)
        return None

    for node in sorted(adjacency):
        found = visit(node, [node])
        if found:
            return found
    return None


def verify_provenance_graph(
    study_path: str | Path,
    *,
    registry_path: str | Path = "data/artifact_registry.jsonl",
    root: str | Path = ".",
    results_root: str | Path | None = None,
) -> dict[str, Any]:
    graph = build_provenance_graph(
        study_path, registry_path=registry_path, root=root, write=False
    )
    errors: list[str] = []
    nodes = {str(node["artifact_id"]): node for node in graph["nodes"]}
    if len(nodes) != len(graph["nodes"]):
        errors.append("duplicate artifact_id")
    for node in graph["nodes"]:
        artifact_id = str(node["artifact_id"])
        required = {
            "artifact_id", "artifact_type", "schema_version", "content_hash",
            "configuration_hash", "study_hash", "parent_artifact_ids", "source_paths",
            "created_at", "evidence_class", "claim_allowed", "validation_status",
        }
        missing = sorted(required - set(node))
        errors.extend(f"{artifact_id}: missing {field}" for field in missing)
        if node.get("claim_allowed") is not False:
            errors.append(f"{artifact_id}: claim_allowed must be false before promotion")
        if len(str(node.get("content_hash", ""))) != 64:
            errors.append(f"{artifact_id}: invalid content hash")
        for parent in node.get("parent_artifact_ids", []):
            if parent not in nodes:
                errors.append(f"{artifact_id}: missing parent {parent}")
        for source in node.get("source_paths", []):
            candidate = Path(source)
            if candidate.is_file() and sha256_file(candidate) != node.get("content_hash") and len(node.get("source_paths", [])) == 1:
                errors.append(f"{artifact_id}: changed artifact hash for {source}")
    for edge in graph["edges"]:
        parent = nodes.get(str(edge["parent_artifact_id"]))
        declared = edge.get("declared_parent_content_hash")
        if parent and declared and declared != parent.get("content_hash"):
            errors.append(
                f"{edge['child_artifact_id']}: changed parent hash for {edge['parent_artifact_id']}"
            )
    cycle = _cycle(nodes, graph["edges"])
    if cycle:
        errors.append("cycle: " + " -> ".join(cycle))
    scan_root = Path(results_root) if results_root else artifact_root(load_study(study_path), root) / "results"
    if scan_root.is_dir():
        registered_paths = {
            str(Path(source).resolve())
            for node in graph["nodes"]
            for source in node.get("source_paths", [])
        }
        for path in scan_root.rglob("*"):
            if path.is_file() and str(path.resolve()) not in registered_paths:
                errors.append(f"unregistered result artifact: {path}")
    return {
        "schema_version": "certgen.maximum_ceiling.provenance_verification.v1",
        "status": "PASS" if not errors else "STALE_ARTIFACT",
        "passed": not errors,
        "study_hash": graph["study_hash"],
        "graph_hash": graph["graph_hash"],
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "errors": errors,
        "claim_allowed": False,
    }


def to_dot(graph: Mapping[str, Any]) -> str:
    lines = ["digraph certgen_provenance {", "  rankdir=LR;"]
    for node in graph["nodes"]:
        identity = str(node["artifact_id"]).replace('"', "\\\"")
        label = f"{node['artifact_type']}\\n{identity[:28]}".replace('"', "\\\"")
        lines.append(f'  "{identity}" [label="{label}"];')
    for edge in graph["edges"]:
        parent = str(edge["parent_artifact_id"]).replace('"', "\\\"")
        child = str(edge["child_artifact_id"]).replace('"', "\\\"")
        lines.append(f'  "{parent}" -> "{child}";')
    lines.append("}")
    return "\n".join(lines) + "\n"
