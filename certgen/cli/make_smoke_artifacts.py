"""Create V1 smoke-only toy artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from certgen.certs.decision import make_decision_certificate
from certgen.cli.validate_config import load_config, validate_config
from certgen.core.enums import EvidenceStatus
from certgen.core.io import make_feature_manifest, save_feature_npz, write_json
from certgen.core.provenance import build_provenance
from certgen.gates.claim_gate import assert_claim_safe
from certgen.metrics.cmmd import cmmd_polynomial
from certgen.metrics.fid import frechet_distance
from certgen.metrics.kid import kid_polynomial
from certgen.metrics.mmd import delta_stream_from_blocks, unbiased_mmd2
from certgen.metrics.registry import metric_record_from_registry
from certgen.reporting.certificate_report import certificate_report_markdown
from certgen.schemas.comparison import ComparisonRecord


def _toy_arrays(max_samples: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(20270623)
    n = max(32, int(max_samples))
    reference = rng.normal(loc=0.0, scale=0.20, size=(n, 8))
    model_a = reference + rng.normal(loc=0.0, scale=0.03, size=(n, 8))
    model_b = reference + 0.18 + rng.normal(loc=0.0, scale=0.03, size=(n, 8))
    return {"reference": reference, "model_a": model_a, "model_b": model_b}


def create_smoke_artifacts(
    *,
    config_path: str | Path,
    out_dir: str | Path,
    compute_metrics: bool = False,
    make_certificate: bool = False,
) -> dict[str, Any]:
    config = load_config(config_path)
    validate_config(config)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    evidence_status = EvidenceStatus.NON_EVIDENCE_SMOKE.value
    arrays = _toy_arrays(int(config["max_samples"]))
    feature_dir = out_dir / "features"
    manifests = []
    for name, array in arrays.items():
        feature_path = feature_dir / f"{name}_features.npz"
        save_feature_npz(array, feature_path)
        manifest = make_feature_manifest(
            dataset_or_model_id=f"smoke_{name}",
            feature_type="toy_feature",
            feature_path=str(feature_path),
            preprocessing={"source": "deterministic numpy smoke arrays", "mode": "toy"},
            evidence_status=evidence_status,
        )
        manifests.append(manifest)
        write_json(manifest, out_dir / "manifests" / f"{name}_feature_manifest.json")

    provenance = build_provenance(
        config=config,
        command="python -m certgen.cli.make_smoke_artifacts",
        input_paths=[str(config_path)],
        notes=["deterministic smoke arrays", "no real model samples"],
    )
    smoke_artifact = {
        "artifact_type": "certgen_v1_smoke",
        "evidence_status": evidence_status,
        "description": "non-evidence smoke artifact for contract validation",
        "manifests": [manifest.feature_manifest_id for manifest in manifests],
        "provenance": provenance,
    }
    write_json(provenance, out_dir / "provenance.json")
    write_json(smoke_artifact, out_dir / "smoke_artifact.json")

    metric_outputs: list[dict[str, Any]] = []
    if compute_metrics:
        reference = arrays["reference"]
        model_a = arrays["model_a"]
        model_b = arrays["model_b"]
        metric_outputs = [
            {
                "metric_name": "kid_poly_descriptive",
                "model_a_distance": kid_polynomial(model_a, reference),
                "model_b_distance": kid_polynomial(model_b, reference),
                "delta_a_minus_b": kid_polynomial(model_a, reference) - kid_polynomial(model_b, reference),
                "evidence_status": evidence_status,
                "limitations": ["toy arrays", "non-evidence smoke output", "polynomial KID is descriptive-only"],
            },
            {
                "metric_name": "cmmd_poly_descriptive",
                "model_a_distance": cmmd_polynomial(model_a, reference),
                "model_b_distance": cmmd_polynomial(model_b, reference),
                "delta_a_minus_b": cmmd_polynomial(model_a, reference) - cmmd_polynomial(model_b, reference),
                "evidence_status": evidence_status,
                "limitations": ["toy arrays", "non-evidence smoke output", "polynomial CMMD is descriptive-only"],
            },
            {
                "metric_name": "mmd_rbf",
                "model_a_distance": unbiased_mmd2(model_a, reference, kernel="rbf", normalize="l2"),
                "model_b_distance": unbiased_mmd2(model_b, reference, kernel="rbf", normalize="l2"),
                "delta_a_minus_b": unbiased_mmd2(model_a, reference, kernel="rbf", normalize="l2")
                - unbiased_mmd2(model_b, reference, kernel="rbf", normalize="l2"),
                "evidence_status": evidence_status,
                "limitations": ["toy arrays", "non-evidence smoke output", "bounded RBF smoke metric"],
            },
            {
                "metric_name": "fid_inception",
                "model_a_distance": frechet_distance(model_a, reference),
                "model_b_distance": frechet_distance(model_b, reference),
                "delta_a_minus_b": frechet_distance(model_a, reference) - frechet_distance(model_b, reference),
                "evidence_status": evidence_status,
                "fid_rigor_status": "descriptive_only",
                "optional_stopping_valid": False,
                "limitations": ["descriptive FID point estimate on toy arrays", "non-evidence smoke output"],
            },
        ]
        write_json({"metrics": metric_outputs, "evidence_status": evidence_status}, out_dir / "metrics" / "smoke_metrics.json")

    certificate_path = None
    report_path = None
    if make_certificate:
        comparison = ComparisonRecord(
            comparison_id="smoke_toy_a_vs_b",
            dataset_id="smoke_reference",
            model_a_id="smoke_model_a",
            model_b_id="smoke_model_b",
            reference_id="smoke_reference",
            metric_name="mmd_rbf",
            alpha=float(config["alpha"]),
            max_samples=int(config["max_samples"]),
            evidence_status=evidence_status,
        )
        metric_record = metric_record_from_registry("mmd_rbf", evidence_status=evidence_status)
        stream = delta_stream_from_blocks(arrays["model_a"], arrays["model_b"], arrays["reference"], block_size=8, kernel="rbf", normalize="l2")
        certificate = make_decision_certificate(
            comparison_record=comparison,
            delta_stream=stream,
            alpha=float(config["alpha"]),
            max_samples=int(config["max_samples"]),
            metric_record=metric_record,
            evidence_status=evidence_status,
        )
        certificate_path = out_dir / "certificates" / "smoke_mmd_rbf_certificate.json"
        write_json(certificate, certificate_path)
        report = certificate_report_markdown(certificate)
        assert_claim_safe(report, evidence_status=evidence_status)
        report_path = out_dir / "reports" / "smoke_certificate_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

    return {
        "out_dir": str(out_dir),
        "evidence_status": evidence_status,
        "manifest_count": len(manifests),
        "metric_count": len(metric_outputs),
        "certificate_path": str(certificate_path) if certificate_path else None,
        "report_path": str(report_path) if report_path else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create non-evidence V1 smoke artifacts.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--compute-metrics", action="store_true")
    parser.add_argument("--make-certificate", action="store_true")
    args = parser.parse_args(argv)
    result = create_smoke_artifacts(
        config_path=args.config,
        out_dir=args.out_dir,
        compute_metrics=args.compute_metrics,
        make_certificate=args.make_certificate,
    )
    print(
        "Created CertGen smoke artifacts: "
        f"out_dir={result['out_dir']}; evidence_status={result['evidence_status']}; "
        f"manifests={result['manifest_count']}; metrics={result['metric_count']}; "
        f"certificate={result['certificate_path'] or 'not_requested'}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
