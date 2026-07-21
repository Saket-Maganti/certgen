"""Canonical nonclaim certificate runner over validated feature bundles."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml  # type: ignore[import-untyped]

from certgen.certs.clean_core import make_clean_metric_certificate
from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json, configuration_hash
from certgen.cvpr.registries import validate_family_record, validate_preregistration
from certgen.metrics.streams import mmd_difference_stream
from certgen.packaging.artifact_registry import append_artifact_entry, build_artifact_entry
from certgen.stats.design_contracts import CSConfig
from certgen.stats.reference_sampling import materialize_reference_draws, validate_reference_draw_plan


DECISION_MAP = {
    "A_certified_better": "A_BETTER",
    "B_certified_better": "B_BETTER",
    "not_decided_at_budget": "UNDECIDED_AT_BUDGET",
}


def _yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"expected mapping in {path}")
    return payload


def _json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object in {path}")
    return payload


def _unique_ids(values: np.ndarray, *, name: str, expected: int) -> list[str]:
    ids = [str(item) for item in np.asarray(values).tolist()]
    if len(ids) != expected or any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError(f"{name} must contain exactly one unique, non-empty ID per row")
    return ids


def load_feature_bundle(path: str | Path) -> dict[str, Any]:
    """Load a no-pickle NPZ with A/B/reference arrays and immutable identities."""

    with np.load(Path(path), allow_pickle=False) as loaded:
        required = {"features_a", "features_b", "features_r", "sample_ids_a", "sample_ids_b", "source_ids_r"}
        missing = sorted(required - set(loaded.files))
        if missing:
            raise ValueError("feature bundle missing arrays: " + ", ".join(missing))
        a = np.asarray(loaded["features_a"], dtype=np.float64)
        b = np.asarray(loaded["features_b"], dtype=np.float64)
        r = np.asarray(loaded["features_r"], dtype=np.float64)
        if any(array.ndim != 2 for array in (a, b, r)):
            raise ValueError("all feature arrays must be two-dimensional")
        if not (a.shape[1] == b.shape[1] == r.shape[1]):
            raise ValueError("feature dimensions do not match")
        if any(not np.all(np.isfinite(array)) for array in (a, b, r)):
            raise ValueError("feature arrays contain NaN or infinity")
        ids_a = _unique_ids(loaded["sample_ids_a"], name="sample_ids_a", expected=len(a))
        ids_b = _unique_ids(loaded["sample_ids_b"], name="sample_ids_b", expected=len(b))
        ids_r = _unique_ids(loaded["source_ids_r"], name="source_ids_r", expected=len(r))
        source_population_ids = None
        reference_draw_ids = None
        if "source_population_ids" in loaded.files or "reference_draw_ids" in loaded.files:
            if not {"source_population_ids", "reference_draw_ids"}.issubset(loaded.files):
                raise ValueError("materialized-reference bundles require both population and draw identities")
            population_raw = np.asarray(loaded["source_population_ids"])
            source_population_ids = _unique_ids(
                population_raw,
                name="source_population_ids",
                expected=len(population_raw),
            )
            reference_draw_ids = _unique_ids(
                loaded["reference_draw_ids"], name="reference_draw_ids", expected=len(r)
            )
    overlap = (set(ids_a) & set(ids_b)) | (set(ids_a) & set(ids_r)) | (set(ids_b) & set(ids_r))
    if overlap:
        raise ValueError("sample identities overlap across A, B, and reference roles")
    return {
        "a": a,
        "b": b,
        "r": r,
        "ids_a": ids_a,
        "ids_b": ids_b,
        "ids_r": ids_r,
        "source_population_ids": source_population_ids,
        "reference_draw_ids": reference_draw_ids,
    }


def _resolve_pair(study: Mapping[str, Any], family: Mapping[str, Any], comparison_id: str) -> tuple[str, str]:
    rows = study.get("model_pairs")
    if not isinstance(rows, list):
        raise ValueError("study.model_pairs must be a list")
    for row in rows:
        if isinstance(row, dict) and row.get("comparison_id") == comparison_id:
            return str(row.get("model_a")), str(row.get("model_b"))
    family_pairs = family.get("model_pairs")
    if not isinstance(family_pairs, list):
        raise ValueError("family.model_pairs must be a list")
    if comparison_id not in family_pairs:
        raise ValueError(f"comparison_id is not registered in family: {comparison_id}")
    raise ValueError(f"study has no model pair definition for {comparison_id}")


def certify_feature_bundle(
    *, study_path: str | Path, family_path: str | Path, feature_bundle_path: str | Path,
    reference_draw_plan_path: str | Path, comparison_id: str, feature_space: str,
    out_path: str | Path, evidence_class: str = "pilot_only",
    fingerprint_path: str | Path | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Issue a deterministic nonclaim certificate or fail before writing."""

    prereg = validate_preregistration(study_path, require_frozen=True)
    if not prereg["passed"]:
        raise ValueError("preregistration invalid: " + "; ".join(prereg["errors"]))
    study = _yaml(study_path)
    fingerprint: dict[str, Any] | None = None
    if fingerprint_path is not None:
        from certgen.cvpr.fingerprint import verify_reproducibility_fingerprint

        fingerprint = _json(fingerprint_path)
        verdict = verify_reproducibility_fingerprint(fingerprint)
        if not verdict["passed"]:
            raise ValueError("reproducibility fingerprint invalid: " + "; ".join(verdict["errors"]))
    if evidence_class == "paper_evidence" and fingerprint is None:
        raise ValueError("paper-evidence certificates require a complete reproducibility fingerprint")
    family = _json(family_path)
    family_verdict = validate_family_record(family, require_frozen=True)
    if not family_verdict["passed"]:
        raise ValueError("family invalid: " + "; ".join(family_verdict["errors"]))
    if family.get("family_id") not in study.get("multiplicity_families", []):
        raise ValueError("family is not registered in the frozen preregistration")
    registered_feature_spaces = family.get("feature_spaces")
    feature_matches = (
        feature_space in set(map(str, registered_feature_spaces))
        if isinstance(registered_feature_spaces, list)
        else feature_space == family.get("feature_space")
    )
    if not feature_matches:
        raise ValueError("feature space does not match the multiplicity family")
    model_a, model_b = _resolve_pair(study, family, comparison_id)
    bundle = load_feature_bundle(feature_bundle_path)
    plan = _json(reference_draw_plan_path)
    if bundle["source_population_ids"] is not None:
        draw_verdict = validate_reference_draw_plan(
            plan, source_ids=bundle["source_population_ids"], min_draws=4
        )
        if not draw_verdict["passed"]:
            raise ValueError("reference draw plan invalid: " + "; ".join(draw_verdict["errors"]))
        draw_ids = [str(row["draw_id"]) for row in plan["draws"]]
        if bundle["reference_draw_ids"] != draw_ids[: len(bundle["r"])] or bundle["ids_r"] != draw_ids[: len(bundle["r"])]:
            raise ValueError("materialized reference feature order differs from the frozen draw plan")
        drawn_r = bundle["r"]
    else:
        draw_verdict = validate_reference_draw_plan(plan, source_ids=bundle["ids_r"], min_draws=4)
        if not draw_verdict["passed"]:
            raise ValueError("reference draw plan invalid: " + "; ".join(draw_verdict["errors"]))
        drawn_r, draw_ids, _ = materialize_reference_draws(
            bundle["r"], bundle["ids_r"], plan, min_draws=4
        )
    count = min(len(bundle["a"]), len(bundle["b"]), len(drawn_r))
    budget_samples = max(int(value) for value in study["sample_budgets"])
    count = min(count, budget_samples)
    if count < 4:
        raise ValueError("feature bundle and draw plan do not support four aligned samples")
    kernel = dict(study.get("kernel") or {})
    if kernel.get("name") not in {"rbf", "mmd_rbf"}:
        raise ValueError("canonical CVPR certificate supports only the bounded RBF route")
    if study.get("stopping_rule") != "first_boundary_crossing_union_hoeffding":
        raise ValueError("unsupported stopping rule for the canonical certificate")
    stream = mmd_difference_stream(
        bundle["a"][:count], bundle["b"][:count], drawn_r[:count], kernel,
        seed=int(study.get("stream_seed", 0)), comparison_id=comparison_id,
        metric_label=str(family["metric"]), evidence_status="real_pilot_non_claim",
        reference_sampling_metadata={
            "sampling_scheme": plan["sampling_scheme"], "plan_sha256": plan["plan_sha256"],
            "draw_ids_sha256": stable_hash_json(draw_ids[:count]), "claim_allowed": False,
        },
    )
    alpha_pair = float(family["alpha_per_hypothesis"])
    config = CSConfig(alpha=alpha_pair, budget_units=len(stream.values), lower_bound=-3.0, upper_bound=3.0, method="hoeffding", seed=int(study.get("stream_seed", 0)))
    raw = make_clean_metric_certificate(
        stream, config,
        feature_hashes={"bundle": file_sha256(feature_bundle_path)},
        command_provenance={"study_hash": configuration_hash(study), "family_hash": family["configuration_hash"], "reference_draw_hash": plan["plan_sha256"]},
    )
    raw_dict = asdict(raw)
    raw_dict["created_at"] = "omitted_from_deterministic_certificate_v1"
    decision = DECISION_MAP[raw.decision]
    study_hash = configuration_hash(study)
    bundle_hash = file_sha256(feature_bundle_path)
    stream_order_hash = stable_hash_json({"sample_ids_a": bundle["ids_a"][:count], "sample_ids_b": bundle["ids_b"][:count], "reference_draw_ids": draw_ids[:count], "stream_seed": int(study.get("stream_seed", 0))})
    stream_identity_hash = stable_hash_json({"comparison_id": comparison_id, "feature_space": feature_space, "feature_bundle_hash": bundle_hash, "reference_draw_hash": plan["plan_sha256"], "stream_order_hash": stream_order_hash, "study_hash": study_hash, "family_hash": family["configuration_hash"], "alpha_pair": alpha_pair})
    family_hypotheses = [row for row in family.get("hypotheses", []) if isinstance(row, Mapping)]
    matching_hypotheses = [
        row for row in family_hypotheses
        if str(row.get("comparison_id")) == comparison_id
        and str(row.get("feature_space")) == feature_space
        and str(row.get("metric")) == str(family["metric"])
        and int(row.get("sample_budget", -1)) == count
    ]
    if family_hypotheses:
        if len(matching_hypotheses) != 1:
            raise ValueError(
                f"certificate must resolve exactly one frozen hypothesis; found {len(matching_hypotheses)}"
            )
        hypothesis_id = str(matching_hypotheses[0]["hypothesis_id"])
    else:
        # Legacy frozen families predate explicit hypothesis enumeration.
        hypothesis_id = f"{comparison_id}__{feature_space}__{family['metric']}__n{count}"
    result: dict[str, Any] = {
        "schema_version": "certgen.cvpr.certificate.v1",
        "study_hash": study_hash,
        "profile": str(study.get("profile_id", "unknown")),
        "hypothesis_id": hypothesis_id,
        "comparison_id": comparison_id,
        "comparison_type": next(
            (
                str(row.get("comparison_type", "registered_pairwise"))
                for row in study.get("model_pairs", [])
                if isinstance(row, Mapping) and row.get("comparison_id") == comparison_id
            ),
            "registered_pairwise",
        ),
        "benchmark": family["benchmark"],
        "model_a": model_a,
        "model_b": model_b,
        "feature_space": feature_space,
        "feature_definition": dict(study.get("feature_definitions", {})).get(feature_space),
        "metric": family["metric"],
        "kernel": family["kernel"],
        "bandwidth": family["bandwidth"],
        "alpha_total": family["alpha_total"],
        "alpha_pair": alpha_pair,
        "sample_budget": count,
        "decision": decision,
        "direction": "A" if decision == "A_BETTER" else ("B" if decision == "B_BETTER" else None),
        "first_decision_n": raw.sample_units_seen * 2 if decision != "UNDECIDED_AT_BUDGET" else None,
        "censored": decision == "UNDECIDED_AT_BUDGET",
        "lower_bound": raw.lower,
        "upper_bound": raw.upper,
        "configuration_hash": study_hash,
        "preprocessing_hash": str(study.get("preprocessing_hash", "TBD_REAL_CACHE_REQUIRED")),
        "reference_population_hash": plan["source_manifest_sha256"],
        "reference_draw_hash": plan["plan_sha256"],
        "control_protocol": "registered_null_split_and_obvious_gap_controls_required_before_family_execution",
        "feature_cache_hashes": {"bundle": bundle_hash},
        "family_id": family["family_id"],
        "family_configuration_hash": family["configuration_hash"],
        "reproducibility_fingerprint": fingerprint.get("fingerprint") if fingerprint else None,
        "analysis_run_id": f"{family['benchmark']}__certificate__{count}__{feature_space}__{study_hash[:12]}__registered-v{study['version']}",
        "parent_run_ids": list(study.get("parent_run_ids", [])),
        "stream_identity_hash": stream_identity_hash,
        "stream_order_hash": stream_order_hash,
        "independent_reuse_prohibited": True,
        "resume_contract": "same stream identity, order, draw, family, alpha, and frozen configuration only; a replay is not a new independent test",
        "alpha_accounting": {"family_id": family["family_id"], "alpha_total": family["alpha_total"], "alpha_pair": alpha_pair, "number_of_hypotheses": family["number_of_hypotheses"]},
        "support_bound": {"lower": -3.0, "upper": 3.0, "justification": "difference of three bounded RBF kernel terms"},
        "evidence_class": evidence_class,
        "evidence_eligibility": "BLOCKED_PENDING_SEPARATE_CLAIM_EVIDENCE_GATE",
        "claim_allowed": False,
        "limitations": ["not_yet_paper_evidence", "single registered comparison", "real lineage gates remain separate"],
        "raw_certificate": raw_dict,
    }
    result["certificate_hash"] = stable_hash_json(result)
    atomic_write_json(result, out_path)
    lineage_path = Path(out_path).with_suffix(".lineage.md")
    lineage_path.write_text(
        "\n".join(
            [
                "# Certificate Lineage Card",
                "",
                f"- Study hash: `{study_hash}`",
                f"- Profile: `{result['profile']}`",
                f"- Family hash: `{family['configuration_hash']}`",
                f"- Hypothesis: `{hypothesis_id}`",
                f"- Comparison: `{comparison_id}`",
                f"- Comparison type: `{result['comparison_type']}`",
                f"- Feature space: `{feature_space}`",
                f"- Feature definition: `{json.dumps(result['feature_definition'], sort_keys=True)}`",
                f"- Reference draw: `{plan['plan_sha256']}`",
                f"- Control protocol: `{result['control_protocol']}`",
                f"- Cache hashes: `{json.dumps(result['feature_cache_hashes'], sort_keys=True)}`",
                f"- Alpha: `{alpha_pair}` (family total `{family['alpha_total']}`)",
                f"- Budget: `{count}`",
                f"- Decision: `{decision}`",
                f"- First crossing: `{result['first_decision_n']}`",
                f"- Censored: `{str(result['censored']).lower()}`",
                "- Support bound: `[-3, 3]`",
                f"- Evidence eligibility: `{result['evidence_eligibility']}`",
                f"- Limitations: {', '.join(result['limitations'])}",
                "- Claim allowed: `false`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if registry_path is not None:
        certificate_entry = append_artifact_entry(
            build_artifact_entry(
                path=out_path,
                artifact_type="cvpr_certificate",
                stage="certificate",
                run_id=result["analysis_run_id"],
                source=str(feature_bundle_path),
                validation_status="certificate_issued_claim_ineligible",
                evidence_class=evidence_class,
                notes="Family-bound certificate; paper promotion remains separately gated.",
            ),
            registry_path,
        )
        append_artifact_entry(
            build_artifact_entry(
                path=lineage_path,
                artifact_type="cvpr_certificate_lineage_card",
                stage="certificate",
                run_id=result["analysis_run_id"],
                source=str(out_path),
                validation_status="lineage_card_written",
                evidence_class=evidence_class,
                parent_artifacts=[certificate_entry["artifact_id"]],
                notes="Human-readable immutable certificate lineage summary.",
            ),
            registry_path,
        )
    return result
