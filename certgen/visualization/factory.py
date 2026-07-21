"""Figure-request validation; empirical rendering is intentionally gated."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json


FIGURE_TYPES = {
    "headline_partial_ranking",
    "anytime_trajectory",
    "decidedness_vs_budget",
    "samples_to_decision",
    "protocol_sensitivity",
    "compute_savings",
    "visual_model_pair_gallery",
    "controlled_failure_gallery",
}

FIGURE_DATA_FIELDS = {
    "headline_partial_ranking": {
        "models",
        "point_estimates",
        "certified_edges",
        "unresolved_edges",
        "feature_disagreements",
    },
    "anytime_trajectory": {
        "n",
        "estimate",
        "lower",
        "upper",
        "first_crossing",
        "maximum_budget",
    },
    "decidedness_vs_budget": {
        "budgets",
        "decided_fraction",
        "undecided_fraction",
        "benchmark",
        "feature_space",
    },
    "samples_to_decision": {"event_times", "censoring_budgets", "feature_spaces"},
    "protocol_sensitivity": {"protocols", "estimate", "lower", "upper"},
    "compute_savings": {
        "comparisons",
        "fixed_budget",
        "first_decision_budget",
        "saved_images",
        "saved_feature_work",
        "saved_generation_work",
    },
    "visual_model_pair_gallery": {"panels", "distribution_claim_disclaimer"},
    "controlled_failure_gallery": {"panels", "failure_modes"},
}


def validate_figure_request(
    request: Mapping[str, Any], artifacts: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    errors: list[str] = []
    required = {
        "figure_id",
        "figure_type",
        "approved_input_artifacts",
        "schema",
        "configuration_hash",
        "claim_gate_status",
        "output_path",
        "caption_metadata",
        "limitations",
    }
    errors.extend(
        f"missing field: {field}" for field in sorted(required - set(request))
    )
    if request.get("figure_type") not in FIGURE_TYPES:
        errors.append("unsupported figure_type")
    artifact_rows = list(artifacts)
    indexed = {str(row.get("artifact_id")): row for row in artifact_rows}
    requested = request.get("approved_input_artifacts")
    if not isinstance(requested, list) or not requested:
        errors.append("approved_input_artifacts must be a non-empty list")
        requested = []
    for artifact_id in requested:
        row = indexed.get(str(artifact_id))
        if row is None:
            errors.append(f"approved input artifact missing: {artifact_id}")
            continue
        if (
            row.get("validation_status") != "paper_approved"
            or row.get("claim_allowed") is not True
        ):
            errors.append(f"artifact is not paper-approved: {artifact_id}")
        if row.get("configuration_hash") != request.get("configuration_hash"):
            errors.append(f"artifact configuration mismatch: {artifact_id}")
    if request.get("claim_gate_status") != "PAPER_EVIDENCE_APPROVED":
        errors.append("claim gate has not approved empirical figure rendering")
    return {
        "passed": not errors,
        "errors": errors,
        "figure_id": request.get("figure_id"),
        "render_allowed": not errors,
    }


def write_planning_contract(
    request: Mapping[str, Any], path: str | Path
) -> dict[str, Any]:
    """Write a non-empirical figure plan without rendering data."""

    payload = {
        **dict(request),
        "status": "PLANNING_ONLY",
        "rendered": False,
        "not_empirical_evidence": True,
        "claim_allowed": False,
    }
    payload["contract_hash"] = stable_hash_json(payload)
    atomic_write_json(payload, path)
    return payload


def _approved_payload(
    request: Mapping[str, Any], artifacts: Iterable[Mapping[str, Any]]
) -> tuple[dict[str, Any], list[Mapping[str, Any]]]:
    rows = list(artifacts)
    verdict = validate_figure_request(request, rows)
    if not verdict["passed"]:
        raise PermissionError(
            "empirical figure rendering blocked: " + "; ".join(verdict["errors"])
        )
    figure_id = str(request["figure_id"])
    payloads = [
        row.get("figure_payloads", {}).get(figure_id)
        for row in rows
        if str(row.get("artifact_id"))
        in set(map(str, request["approved_input_artifacts"]))
    ]
    payloads = [payload for payload in payloads if isinstance(payload, dict)]
    if len(payloads) != 1:
        raise ValueError(
            "exactly one approved artifact must provide the figure payload"
        )
    payload = dict(payloads[0])
    required = FIGURE_DATA_FIELDS[str(request["figure_type"])]
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(
            "approved figure payload is missing fields: " + ", ".join(missing)
        )
    return payload, rows


def render_approved_figure(
    request: Mapping[str, Any], artifacts: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    """Render one future empirical figure only after the paper evidence gate.

    This function is not exercised in the pre-execution build. It performs no
    artifact discovery: every input must already be approved and supplied.
    """

    payload, artifact_rows = _approved_payload(request, artifacts)
    output = Path(str(request["output_path"]))
    if output.exists():
        raise FileExistsError(f"refusing to overwrite figure: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    import matplotlib.pyplot as plt
    import numpy as np

    figure_type = str(request["figure_type"])
    if figure_type == "headline_partial_ranking":
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        models = list(map(str, payload["models"]))
        axes[0].barh(
            models, [float(payload["point_estimates"][model]) for model in models]
        )
        axes[0].set_title("Point estimates (descriptive)")
        angles = np.linspace(0, 2 * np.pi, len(models), endpoint=False)
        node_positions = {
            model: (np.cos(angle), np.sin(angle))
            for model, angle in zip(models, angles)
        }
        for model, (x_value, y_value) in node_positions.items():
            axes[1].scatter([x_value], [y_value])
            axes[1].text(x_value, y_value, model)
        for edge in payload["certified_edges"]:
            start, end = node_positions[str(edge["winner"])], node_positions[str(edge["loser"])]
            axes[1].annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->"})
        axes[1].set_title(
            f"Certified partial graph; unresolved={len(payload['unresolved_edges'])}; disagreements={len(payload['feature_disagreements'])}"
        )
        axes[1].axis("off")
    elif figure_type == "anytime_trajectory":
        fig, axis = plt.subplots(figsize=(8, 5))
        n_values = payload["n"]
        axis.plot(n_values, payload["estimate"], label="running estimate")
        axis.fill_between(
            n_values,
            payload["lower"],
            payload["upper"],
            alpha=0.25,
            label="confidence sequence",
        )
        axis.axhline(0.0, color="black", linewidth=1)
        axis.axvline(payload["maximum_budget"], linestyle=":", label="maximum budget")
        if payload["first_crossing"] is not None:
            axis.axvline(
                payload["first_crossing"], linestyle="--", label="first crossing"
            )
        axis.legend()
        axis.set_xlabel("samples")
        axis.set_ylabel("registered comparison estimand")
    elif figure_type == "decidedness_vs_budget":
        fig, axis = plt.subplots(figsize=(8, 5))
        budgets = payload["budgets"]
        axis.plot(budgets, payload["decided_fraction"], marker="o", label="decided")
        axis.plot(budgets, payload["undecided_fraction"], marker="o", label="undecided")
        axis.set_title(f"{payload['benchmark']} / {payload['feature_space']}")
        axis.legend()
        axis.set_ylim(0, 1)
    elif figure_type == "samples_to_decision":
        fig, axis = plt.subplots(figsize=(8, 5))
        axis.scatter(
            payload["event_times"],
            [1] * len(payload["event_times"]),
            label="decided",
            marker="o",
        )
        axis.scatter(
            payload["censoring_budgets"],
            [0] * len(payload["censoring_budgets"]),
            label="right-censored",
            marker="x",
        )
        axis.set_yticks([0, 1], ["censored", "decided"])
        axis.legend()
        axis.set_xlabel("samples")
    elif figure_type == "protocol_sensitivity":
        fig, axis = plt.subplots(figsize=(9, 5))
        protocol_positions = np.arange(len(payload["protocols"]))
        estimates = np.asarray(payload["estimate"], dtype=float)
        errors = np.vstack(
            (
                estimates - np.asarray(payload["lower"]),
                np.asarray(payload["upper"]) - estimates,
            )
        )
        axis.errorbar(protocol_positions, estimates, yerr=errors, fmt="o")
        axis.axhline(0.0, color="black", linewidth=1)
        axis.set_xticks(protocol_positions, payload["protocols"], rotation=30, ha="right")
    elif figure_type == "compute_savings":
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        comparison_positions = np.arange(len(payload["comparisons"]))
        axes[0].bar(
            comparison_positions - 0.2, payload["fixed_budget"], width=0.4, label="fixed budget"
        )
        axes[0].bar(
            comparison_positions + 0.2,
            payload["first_decision_budget"],
            width=0.4,
            label="first decision",
        )
        axes[0].set_xticks(comparison_positions, payload["comparisons"], rotation=30, ha="right")
        axes[0].legend()
        axes[1].bar(comparison_positions, payload["saved_images"], label="images")
        axes[1].plot(
            comparison_positions, payload["saved_feature_work"], marker="o", label="feature work"
        )
        axes[1].plot(
            comparison_positions,
            payload["saved_generation_work"],
            marker="x",
            label="generation work",
        )
        axes[1].legend()
    else:
        panels = list(payload["panels"])
        fig, axes = plt.subplots(
            1, max(1, len(panels)), figsize=(4 * max(1, len(panels)), 4)
        )
        axes = np.atleast_1d(axes)
        for axis, panel in zip(axes, panels):
            image_path = Path(str(panel["image_path"]))
            if not image_path.is_file():
                raise FileNotFoundError(f"approved gallery image missing: {image_path}")
            axis.imshow(plt.imread(image_path))
            axis.axis("off")
            axis.set_title(str(panel.get("caption", panel.get("failure_mode", ""))))
        fig.text(
            0.5,
            0.01,
            str(
                payload.get(
                    "distribution_claim_disclaimer",
                    "Selected images do not prove distribution-level claims.",
                )
            ),
            ha="center",
        )
    fig.suptitle(
        str(request.get("caption_metadata", {}).get("title", request["figure_id"]))
    )
    fig.tight_layout()
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.stem}.", suffix=output.suffix, dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        fig.savefig(temporary, bbox_inches="tight")
        os.replace(temporary, output)
    finally:
        plt.close(fig)
        temporary.unlink(missing_ok=True)
    result = {
        "figure_id": request["figure_id"],
        "figure_type": figure_type,
        "output_path": str(output),
        "output_hash": file_sha256(output),
        "approved_input_artifacts": list(request["approved_input_artifacts"]),
        "configuration_hash": request["configuration_hash"],
        "claim_gate_status": request["claim_gate_status"],
        "caption_metadata": request["caption_metadata"],
        "limitations": request["limitations"],
        "claim_allowed": all(
            row.get("claim_allowed") is True
            for row in artifact_rows
            if str(row.get("artifact_id"))
            in set(map(str, request["approved_input_artifacts"]))
        ),
    }
    atomic_write_json(result, output.with_suffix(output.suffix + ".json"))
    return result
