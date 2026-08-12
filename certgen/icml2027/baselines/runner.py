"""CPU baseline implementations over identity-aligned feature bundles."""

from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial.distance import cdist  # type: ignore[import-untyped]

from certgen.icml2027.common import file_sha256, load_mapping, stable_hash, write_json
from certgen.icml2027.sequential import evaluate_stream
from certgen.metrics.fid import frechet_distance
from certgen.metrics.kid import kid_polynomial
from certgen.metrics.mmd import unbiased_mmd2


BASELINES: dict[str, dict[str, Any]] = {
    "fid": {"method_family": "feature_moments", "supports_streaming": False},
    "kid": {"method_family": "polynomial_mmd", "supports_streaming": False},
    "fixed_rbf_mmd": {"method_family": "kernel_two_sample", "supports_streaming": False},
    "permutation_mmd": {"method_family": "randomization_test", "supports_streaming": False},
    "bootstrap_mmd": {"method_family": "bootstrap_interval", "supports_streaming": False},
    "c2st": {"method_family": "classifier_two_sample_centroid_legacy_alias", "supports_streaming": False},
    "c2st_centroid": {"method_family": "classifier_two_sample_centroid", "supports_streaming": False},
    "c2st_logistic": {
        "method_family": "classifier_two_sample_logistic_permutation",
        "supports_streaming": False,
    },
    "precision_recall": {"method_family": "support_diagnostic", "supports_streaming": False},
    "density_coverage": {"method_family": "support_diagnostic", "supports_streaming": False},
    "nearest_neighbor": {"method_family": "nearest_neighbor_diagnostic", "supports_streaming": False},
    "naive_repeated": {"method_family": "sequential_mean", "supports_streaming": True},
    "alpha_spending": {"method_family": "sequential_mean", "supports_streaming": True},
    "fixed_bonferroni": {"method_family": "fixed_family", "supports_streaming": False},
    "certgen_anytime": {"method_family": "anytime_valid_mean", "supports_streaming": True},
}


def _validate_bundle(path: str | Path) -> dict[str, np.ndarray]:
    source = Path(path)
    with np.load(source, allow_pickle=False) as loaded:
        required = {"reference", "model_a", "model_b", "reference_ids", "model_a_ids", "model_b_ids"}
        missing = sorted(required - set(loaded.files))
        if missing:
            raise ValueError(f"feature bundle missing keys: {missing}")
        bundle = {key: np.asarray(loaded[key]) for key in required}
        if "delta_stream" in loaded:
            bundle["delta_stream"] = np.asarray(loaded["delta_stream"], dtype=float)
    for role in ("reference", "model_a", "model_b"):
        array = np.asarray(bundle[role], dtype=float)
        ids = np.asarray(bundle[f"{role}_ids"])
        if array.ndim != 2 or not len(array) or len(array) != len(ids):
            raise ValueError(f"invalid {role} feature/ID alignment")
        if len(set(str(item) for item in ids.tolist())) != len(ids):
            raise ValueError(f"duplicate {role} sample IDs")
        if not np.all(np.isfinite(array)):
            raise ValueError(f"nonfinite {role} features")
        bundle[role] = array
    dimensions = {bundle[role].shape[1] for role in ("reference", "model_a", "model_b")}
    if len(dimensions) != 1:
        raise ValueError("feature dimensions differ")
    return bundle


def _rbf_bandwidth(*arrays: np.ndarray) -> float:
    joined = np.concatenate(arrays, axis=0)
    if len(joined) > 512:
        joined = joined[np.linspace(0, len(joined) - 1, 512, dtype=int)]
    distances = cdist(joined, joined, metric="sqeuclidean")
    positive = distances[distances > 0]
    return float(math.sqrt(max(float(np.median(positive)) / 2.0, 1e-12))) if len(positive) else 1.0


def _distances(bundle: dict[str, np.ndarray], bandwidth: float) -> tuple[float, float, float]:
    kwargs = {"bandwidth": bandwidth}
    a = unbiased_mmd2(bundle["model_a"], bundle["reference"], kernel="rbf", **kwargs)
    b = unbiased_mmd2(bundle["model_b"], bundle["reference"], kernel="rbf", **kwargs)
    return a, b, a - b


def _permutation_delta(
    bundle: dict[str, np.ndarray], bandwidth: float, rng: np.random.Generator, repetitions: int
) -> dict[str, Any]:
    a, b, observed = _distances(bundle, bandwidth)
    joined = np.concatenate([bundle["model_a"], bundle["model_b"]], axis=0)
    n_a = len(bundle["model_a"])
    null: np.ndarray = np.empty(repetitions, dtype=float)
    for index in range(repetitions):
        order = rng.permutation(len(joined))
        permuted = {**bundle, "model_a": joined[order[:n_a]], "model_b": joined[order[n_a:]]}
        null[index] = _distances(permuted, bandwidth)[2]
    p_value = (1 + int(np.count_nonzero(np.abs(null) >= abs(observed)))) / (repetitions + 1)
    return {"distance_a": a, "distance_b": b, "estimate": observed, "p_value": p_value, "repetitions": repetitions}


def _bootstrap_delta(
    bundle: dict[str, np.ndarray], bandwidth: float, rng: np.random.Generator, repetitions: int, alpha: float
) -> dict[str, Any]:
    a, b, observed = _distances(bundle, bandwidth)
    bootstrap_values: np.ndarray = np.empty(repetitions, dtype=float)
    for index in range(repetitions):
        resampled = {
            **bundle,
            "reference": bundle["reference"][rng.integers(0, len(bundle["reference"]), len(bundle["reference"]))],
            "model_a": bundle["model_a"][rng.integers(0, len(bundle["model_a"]), len(bundle["model_a"]))],
            "model_b": bundle["model_b"][rng.integers(0, len(bundle["model_b"]), len(bundle["model_b"]))],
        }
        bootstrap_values[index] = _distances(resampled, bandwidth)[2]
    lower, upper = np.quantile(bootstrap_values, [alpha / 2, 1 - alpha / 2]).tolist()
    return {
        "distance_a": a,
        "distance_b": b,
        "estimate": observed,
        "ci_lower": float(lower),
        "ci_upper": float(upper),
        "repetitions": repetitions,
    }


def _c2st_accuracy(x: np.ndarray, y: np.ndarray, rng: np.random.Generator, folds: int = 5) -> float:
    features = np.concatenate([x, y], axis=0)
    labels = np.concatenate([np.zeros(len(x), dtype=int), np.ones(len(y), dtype=int)])
    order = rng.permutation(len(features))
    fold_ids: np.ndarray = np.arange(len(features)) % folds
    predictions: np.ndarray = np.empty(len(features), dtype=int)
    for fold in range(folds):
        test_indices = order[fold_ids == fold]
        train_indices = order[fold_ids != fold]
        train_x = features[train_indices]
        train_y = labels[train_indices]
        mean_0 = train_x[train_y == 0].mean(axis=0)
        mean_1 = train_x[train_y == 1].mean(axis=0)
        distance_0 = np.sum((features[test_indices] - mean_0) ** 2, axis=1)
        distance_1 = np.sum((features[test_indices] - mean_1) ** 2, axis=1)
        predictions[test_indices] = (distance_1 < distance_0).astype(int)
    return float(np.mean(predictions == labels))


def _c2st_logistic(
    x: np.ndarray,
    y: np.ndarray,
    *,
    seed: int,
    folds: int = 5,
    permutations: int = 99,
) -> dict[str, Any]:
    """Leakage-safe standardized logistic C2ST with a permutation p-value."""

    from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
    from sklearn.metrics import accuracy_score  # type: ignore[import-untyped]
    from sklearn.model_selection import StratifiedKFold  # type: ignore[import-untyped]
    from sklearn.pipeline import make_pipeline  # type: ignore[import-untyped]
    from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

    features = np.concatenate([x, y], axis=0)
    labels = np.concatenate([np.zeros(len(x), dtype=int), np.ones(len(y), dtype=int)])
    if folds < 2 or folds > min(len(x), len(y)):
        raise ValueError("c2st_folds must be between 2 and the smaller class size")
    if permutations < 0:
        raise ValueError("c2st_permutations must be nonnegative")
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    splits = list(splitter.split(features, labels))

    def score(targets: np.ndarray) -> float:
        predictions: np.ndarray = np.empty(len(targets), dtype=int)
        for train_indices, test_indices in splits:
            pipeline = make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    solver="lbfgs",
                    max_iter=1000,
                    random_state=seed,
                ),
            )
            pipeline.fit(features[train_indices], targets[train_indices])
            predictions[test_indices] = pipeline.predict(features[test_indices])
        return float(accuracy_score(targets, predictions))

    observed = score(labels)
    rng = np.random.default_rng(seed)
    null = np.asarray([score(rng.permutation(labels)) for _ in range(permutations)], dtype=np.float64)
    p_value = (1 + int(np.count_nonzero(null >= observed))) / (permutations + 1)
    return {
        "accuracy": observed,
        "chance_accuracy": 0.5,
        "permutation_p_value": p_value,
        "permutations": permutations,
        "folds": folds,
        "preprocessing": "StandardScaler fit within each training fold",
        "classifier": "sklearn.linear_model.LogisticRegression(solver=lbfgs,max_iter=1000)",
    }


def _knn_support(reference: np.ndarray, generated: np.ndarray, k: int = 3) -> dict[str, float]:
    if len(reference) <= k or len(generated) <= k:
        raise ValueError("support diagnostics require more rows than k")
    rr = cdist(reference, reference)
    np.fill_diagonal(rr, np.inf)
    radii_r = np.partition(rr, k - 1, axis=1)[:, k - 1]
    gg = cdist(generated, generated)
    np.fill_diagonal(gg, np.inf)
    radii_g = np.partition(gg, k - 1, axis=1)[:, k - 1]
    gr = cdist(generated, reference)
    generated_in_reference = gr <= radii_r[None, :]
    reference_in_generated = gr <= radii_g[:, None]
    precision = float(np.mean(np.any(generated_in_reference, axis=1)))
    recall = float(np.mean(np.any(reference_in_generated, axis=0)))
    density = float(np.mean(np.sum(generated_in_reference, axis=1) / k))
    coverage = float(np.mean(np.min(gr, axis=0) <= radii_r))
    return {
        "precision": precision,
        "recall": recall,
        "density": density,
        "coverage": coverage,
        "mean_nearest_distance": float(np.mean(np.min(gr, axis=1))),
    }


def _delta_stream(bundle: dict[str, np.ndarray], bandwidth: float, block_size: int = 8) -> np.ndarray:
    if "delta_stream" in bundle:
        provided = np.asarray(bundle["delta_stream"], dtype=float)
        if provided.ndim != 1 or not np.all(np.isfinite(provided)) or np.any(np.abs(provided) > 1):
            raise ValueError("delta_stream must be finite, one-dimensional, and bounded in [-1,1]")
        return provided
    count = min(len(bundle["reference"]), len(bundle["model_a"]), len(bundle["model_b"]))
    block_values: list[float] = []
    for start in range(0, count, block_size):
        stop = min(start + block_size, count)
        if stop - start < 2:
            continue
        local = {key: value[start:stop] if key in {"reference", "model_a", "model_b"} else value for key, value in bundle.items()}
        block_values.append(float(np.clip(_distances(local, bandwidth)[2], -1.0, 1.0)))
    return np.asarray(block_values, dtype=float)


def _comparison_decision(delta: float, significant: bool) -> str:
    if not significant:
        return "UNRESOLVED"
    return "A_BETTER" if delta < 0 else "B_BETTER"


def run_baseline(
    baseline_id: str,
    feature_bundle: str | Path,
    study_path: str | Path,
    out_path: str | Path,
) -> dict[str, Any]:
    if baseline_id not in BASELINES:
        raise ValueError(f"unknown baseline {baseline_id!r}; choose from {sorted(BASELINES)}")
    study = load_mapping(study_path)
    alpha = float(study.get("alpha", 0.05))
    seed = int(study.get("master_seed", 2027))
    repetitions = int(study.get("baseline_repetitions", 99))
    rng = np.random.default_rng(seed)
    bundle = _validate_bundle(feature_bundle)
    bandwidth = float(study.get("bandwidth", _rbf_bandwidth(bundle["reference"], bundle["model_a"], bundle["model_b"])))
    started = time.perf_counter()
    result: dict[str, Any]
    if baseline_id == "fid":
        a = frechet_distance(bundle["model_a"], bundle["reference"])
        b = frechet_distance(bundle["model_b"], bundle["reference"])
        result = {"distance_a": a, "distance_b": b, "estimate": a - b, "decision": "DESCRIPTIVE_ONLY"}
    elif baseline_id == "kid":
        a = kid_polynomial(bundle["model_a"], bundle["reference"])
        b = kid_polynomial(bundle["model_b"], bundle["reference"])
        result = {"distance_a": a, "distance_b": b, "estimate": a - b, "decision": "DESCRIPTIVE_ONLY"}
    elif baseline_id == "fixed_rbf_mmd":
        a, b, delta = _distances(bundle, bandwidth)
        result = {"distance_a": a, "distance_b": b, "estimate": delta, "decision": "DESCRIPTIVE_ONLY"}
    elif baseline_id == "permutation_mmd":
        result = _permutation_delta(bundle, bandwidth, rng, repetitions)
        result["decision"] = _comparison_decision(float(result["estimate"]), float(result["p_value"]) <= alpha)
    elif baseline_id == "bootstrap_mmd":
        result = _bootstrap_delta(bundle, bandwidth, rng, repetitions, alpha)
        significant = float(result["ci_upper"]) < 0 or float(result["ci_lower"]) > 0
        result["decision"] = _comparison_decision(float(result["estimate"]), significant)
    elif baseline_id in {"c2st", "c2st_centroid"}:
        score_a = _c2st_accuracy(bundle["reference"], bundle["model_a"], rng)
        score_b = _c2st_accuracy(bundle["reference"], bundle["model_b"], rng)
        result = {"score_a": score_a, "score_b": score_b, "estimate": score_a - score_b, "decision": "DESCRIPTIVE_ONLY"}
    elif baseline_id == "c2st_logistic":
        folds = int(study.get("c2st_folds", 5))
        permutations = int(study.get("c2st_permutations", repetitions))
        logistic_a = _c2st_logistic(
            bundle["reference"], bundle["model_a"], seed=seed + 101, folds=folds, permutations=permutations
        )
        logistic_b = _c2st_logistic(
            bundle["reference"], bundle["model_b"], seed=seed + 211, folds=folds, permutations=permutations
        )
        result = {
            "model_a": logistic_a,
            "model_b": logistic_b,
            "estimate": float(logistic_a["accuracy"] - logistic_b["accuracy"]),
            "decision": "DESCRIPTIVE_ONLY_SEPARATE_PERMUTATION_TESTS",
        }
    elif baseline_id in {"precision_recall", "density_coverage", "nearest_neighbor"}:
        support_a = _knn_support(bundle["reference"], bundle["model_a"])
        support_b = _knn_support(bundle["reference"], bundle["model_b"])
        result = {"model_a": support_a, "model_b": support_b, "decision": "DESCRIPTIVE_ONLY"}
    else:
        stream = _delta_stream(bundle, bandwidth, int(study.get("block_size", 8)))
        rule = {
            "naive_repeated": "naive_repeated",
            "alpha_spending": "alpha_spending",
            "fixed_bonferroni": "fixed_n",
            "certgen_anytime": "anytime",
        }[baseline_id]
        family_size = int(study.get("family_size", 1))
        test_alpha = alpha / family_size if baseline_id == "fixed_bonferroni" else alpha
        trace = evaluate_stream(
            stream,
            alpha=test_alpha,
            rule=rule,
            looks=study.get("looks"),
            true_mean=float(study.get("true_mean", 0.0)),
        )
        result = {
            "estimate": trace.mean,
            "ci_lower": trace.lower,
            "ci_upper": trace.upper,
            "confidence_width": trace.confidence_width,
            "decision": trace.decision,
            "stopping_time": trace.stopping_time,
            "coverage": trace.coverage,
        }
    payload = {
        "schema_version": "certgen.icml2027.baseline_result.v1",
        "baseline_id": baseline_id,
        "baseline_contract": BASELINES[baseline_id],
        "feature_bundle": str(feature_bundle),
        "feature_bundle_sha256": file_sha256(feature_bundle),
        "study": str(study_path),
        "study_hash": stable_hash(study),
        "sample_ids_hashes": {
            role: stable_hash([str(item) for item in bundle[f"{role}_ids"].tolist()])
            for role in ("reference", "model_a", "model_b")
        },
        "alpha": alpha,
        "bandwidth": bandwidth,
        "runtime_seconds": time.perf_counter() - started,
        "result": result,
        "synthetic_validation_only": bool(study.get("synthetic_validation_only", False)),
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
    write_json(out_path, payload)
    return payload
