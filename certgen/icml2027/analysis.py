"""Result-agnostic CPU analyses for prefixes, costs, and contamination."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import read_rows, stable_hash, write_csv, write_json
from certgen.icml2027.sequential import evaluate_stream


DEFAULT_PREFIXES = (100, 250, 500, 1000, 2000, 5000, 10000)
COST_FIELDS = (
    "GPU_seconds",
    "CPU_seconds",
    "wall_seconds",
    "images_generated",
    "images_featured",
    "feature_vectors_computed",
    "bytes_read",
    "bytes_written",
    "disk_peak",
    "VRAM_peak",
    "RAM_peak",
    "model_load_seconds",
    "dependency_install_seconds",
    "samples_to_decision",
    "percent_budget_saved",
)


def deterministic_prefix_ids(sample_ids: list[str], budget: int) -> list[str]:
    if budget < 0 or budget > len(sample_ids):
        raise ValueError("prefix budget is outside the frozen maximum stream")
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("maximum stream contains duplicate sample IDs")
    return sample_ids[:budget]


def samples_to_decision(
    input_path: str | Path,
    out_path: str | Path,
    *,
    prefixes: tuple[int, ...] = DEFAULT_PREFIXES,
) -> dict[str, Any]:
    rows = read_rows(input_path)
    output: list[dict[str, Any]] = []
    for row in rows:
        values = row.get("stream")
        sample_ids = row.get("sample_ids")
        if isinstance(values, str):
            values = json.loads(values)
        if isinstance(sample_ids, str):
            sample_ids = json.loads(sample_ids)
        if not isinstance(values, list) or not isinstance(sample_ids, list) or len(values) != len(sample_ids):
            raise ValueError("each input row requires aligned stream and sample_ids arrays")
        maximum = len(values)
        valid_prefixes = [budget for budget in prefixes if budget <= maximum]
        if maximum not in valid_prefixes:
            valid_prefixes.append(maximum)
        first_decision: int | None = None
        for budget in sorted(set(valid_prefixes)):
            prefix_ids = deterministic_prefix_ids([str(value) for value in sample_ids], budget)
            started = time.perf_counter()
            trace = evaluate_stream(
                [float(value) for value in values[:budget]],
                alpha=float(row.get("alpha", 0.05)),
                rule=str(row.get("stopping_rule", "anytime")),
                looks=row.get("looks"),
                true_mean=float(row.get("true_mean", 0.0)),
            )
            if first_decision is None and trace.decision not in {"UNRESOLVED", "INVALID"}:
                first_decision = trace.stopping_time
            samples_saved = max(0, maximum - (first_decision or maximum))
            output.append(
                {
                    "method": row.get("method", "certgen_anytime"),
                    "comparison": row.get("comparison", "unspecified"),
                    "feature_space": row.get("feature_space", "synthetic"),
                    "budget": budget,
                    "decision": trace.decision,
                    "first_decision_n": first_decision or "",
                    "censored": first_decision is None,
                    "confidence_width": trace.confidence_width,
                    "runtime": time.perf_counter() - started,
                    "samples_saved_vs_full_budget": samples_saved,
                    "percent_saved": 100.0 * samples_saved / maximum,
                    "prefix_ids_hash": stable_hash(prefix_ids),
                    "outcome_adaptive_prefix_selection": False,
                    "claim_allowed": False,
                }
            )
    write_csv(out_path, output)
    return {
        "schema_version": "certgen.icml2027.samples_to_decision_summary.v1",
        "rows": len(output),
        "prefixes": sorted({int(row["budget"]) for row in output}),
        "claim_allowed": False,
    }


def cost_to_decision(input_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    rows = read_rows(input_path)
    output: list[dict[str, Any]] = []
    for row in rows:
        status = str(row.get("measurement_status", ""))
        if status not in {"measured", "planning_estimate", "unknown"}:
            raise ValueError("measurement_status must be measured, planning_estimate, or unknown")
        normalized: dict[str, Any] = {
            "study_id": row.get("study_id", ""),
            "stage": row.get("stage", ""),
            "comparison": row.get("comparison", ""),
            "measurement_status": status,
            "claim_allowed": False,
        }
        for field in COST_FIELDS:
            value = row.get(field, "")
            if status == "unknown" and value not in {"", None, "unknown"}:
                raise ValueError(f"unknown cost row must not contain a numeric {field}")
            normalized[field] = value if value not in {None, "unknown"} else ""
        output.append(normalized)
    write_csv(out_path, output)
    totals: dict[str, dict[str, float]] = {}
    for status in ("measured", "planning_estimate"):
        selected = [row for row in output if row["measurement_status"] == status]
        totals[status] = {
            field: sum(float(row[field]) for row in selected if row[field] not in {"", None})
            for field in COST_FIELDS
        }
    return {
        "schema_version": "certgen.icml2027.cost_summary.v1",
        "rows": len(output),
        "totals_kept_separate": totals,
        "claim_allowed": False,
    }


def _difference_hash(path: Path) -> str | None:
    try:
        from PIL import Image

        with Image.open(path) as image:
            gray = image.convert("L").resize((9, 8))
            pixels = np.asarray(gray, dtype=np.int16)
        bits = pixels[:, 1:] > pixels[:, :-1]
        return f"{int(''.join('1' if item else '0' for item in bits.flat), 2):016x}"
    except Exception:
        return None


def _hamming(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def analyze_duplicates(
    roots: list[str | Path],
    out_path: str | Path,
    *,
    near_threshold: int = 4,
) -> dict[str, Any]:
    files: list[tuple[str, Path]] = []
    for raw in roots:
        root = Path(raw)
        role = root.name
        files.extend((role, path) for path in sorted(root.rglob("*")) if path.is_file())
    inventory: list[dict[str, Any]] = []
    for role, path in files:
        data = path.read_bytes()
        inventory.append(
            {
                "role": role,
                "path": str(path),
                "sha256": hashlib.sha256(data).hexdigest(),
                "perceptual_hash": _difference_hash(path),
                "bytes": len(data),
            }
        )
    exact_groups: dict[str, list[dict[str, Any]]] = {}
    for row in inventory:
        exact_groups.setdefault(str(row["sha256"]), []).append(row)
    exact = [group for group in exact_groups.values() if len(group) > 1]
    near: list[dict[str, Any]] = []
    for index, left in enumerate(inventory):
        if not left["perceptual_hash"]:
            continue
        for right in inventory[index + 1 :]:
            if not right["perceptual_hash"] or left["sha256"] == right["sha256"]:
                continue
            distance = _hamming(str(left["perceptual_hash"]), str(right["perceptual_hash"]))
            if distance <= near_threshold:
                near.append({"left": left["path"], "right": right["path"], "hamming_distance": distance})
    cross_set = [group for group in exact if len({str(row["role"]) for row in group}) > 1]
    within_generated = [group for group in exact if len({str(row["role"]) for row in group}) == 1]
    payload = {
        "schema_version": "certgen.icml2027.duplicate_audit.v1",
        "files": len(inventory),
        "inventory": inventory,
        "exact_duplicate_groups": exact,
        "near_duplicate_pairs": near,
        "cross_set_leakage_groups": cross_set,
        "within_set_duplicate_groups": within_generated,
        "passed": not exact and not near,
        "claim_allowed": False,
    }
    write_json(out_path, payload)
    return payload


def validate_cost_record(record: dict[str, Any]) -> None:
    status = record.get("measurement_status")
    if status not in {"measured", "planning_estimate", "unknown"}:
        raise ValueError("invalid measurement_status")
    if status == "measured" and record.get("planning_estimate"):
        raise ValueError("measured records cannot be labeled planning estimates")
