"""Certificate replay and determinism checks."""

from __future__ import annotations

from pathlib import Path

from certgen.certs.api import certify_clean_metric_comparison
from certgen.core.io import read_json, write_json


def replay_certificate(certificate_path: str | Path, out: str | Path, json_out: str | Path) -> dict:
    cert = read_json(certificate_path)
    provenance = cert.get("command_provenance") or {}
    input_paths = provenance.get("input_paths") or []
    if len(input_paths) < 3 or not all(Path(p).exists() for p in input_paths[:3]):
        payload = {
            "replay_status": "blocked_missing_inputs",
            "claim_allowed": False,
            "evidence_status": cert.get("evidence_status", "dry_run_only"),
            "errors": ["missing feature inputs"],
        }
    else:
        tmp_out = Path(json_out).with_suffix(".replayed_certificate.json")
        parameters = provenance.get("parameters") or {}
        method_label = cert.get("method_label", "")
        method = parameters.get("method")
        if not method:
            method = "betting" if "betting" in method_label else "hoeffding" if "hoeffding" in method_label else "empirical_bernstein"
        try:
            replayed = certify_clean_metric_comparison(
                input_paths[0],
                input_paths[1],
                input_paths[2],
                parameters.get("metric_label") or cert.get("metric_label", cert.get("metric", "mmd_rbf")),
                parameters.get("kernel_config") or {},
                {
                    "alpha": cert.get("alpha", 0.05),
                    "budget_units": cert.get("budget_units", cert.get("max_samples", 40)),
                    "method": method,
                    "seed": int(parameters.get("seed", 0)),
                    "block_size": parameters.get("block_size"),
                    "metric_reproduction_audit": parameters.get("metric_reproduction_audit"),
                },
                cert.get("comparison_id", "replay"),
                cert.get("evidence_status", "smoke_only"),
                str(tmp_out),
            )
            payload = {
                "replay_status": "passed" if replayed.decision == cert.get("decision") and replayed.stream_hash == cert.get("stream_hash") else "failed_mismatch",
                "original_decision": cert.get("decision"),
                "replayed_decision": replayed.decision,
                "original_stream_hash": cert.get("stream_hash"),
                "replayed_stream_hash": replayed.stream_hash,
                "claim_allowed": False,
                "evidence_status": cert.get("evidence_status", "dry_run_only"),
            }
        except ValueError as exc:
            payload = {
                "replay_status": "blocked_policy",
                "claim_allowed": False,
                "evidence_status": cert.get("evidence_status", "dry_run_only"),
                "errors": [str(exc)],
            }
    lines = ["# Certificate Replay Report", "", "`NO_REAL_EVIDENCE`", "", f"Replay status: `{payload['replay_status']}`", "Claim allowed: `False`"]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload
