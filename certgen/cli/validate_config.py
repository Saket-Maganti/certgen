"""Validate CertGen V1 smoke configs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.enums import EvidenceStatus
from certgen.gates.evidence_gate import validate_evidence_status


REQUIRED_TOP_LEVEL_FIELDS = {
    "project",
    "version",
    "mode",
    "alpha",
    "max_samples",
    "metrics",
    "fid_policy",
    "allow_real_evidence",
    "evidence_status",
}


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml
        except Exception as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("PyYAML is required for YAML configs; use JSON fallback if PyYAML is unavailable") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def validate_config(config: dict[str, Any]) -> list[str]:
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(config))
    if missing:
        raise ValueError(f"Missing required config fields: {', '.join(missing)}")
    if config["project"] != "CertGen":
        raise ValueError("project must be CertGen")
    if config["mode"] != "smoke":
        raise ValueError("V1 config validator currently supports smoke mode only")
    if bool(config["allow_real_evidence"]):
        raise ValueError("allow_real_evidence must be false for V1 smoke")
    if config["evidence_status"] != EvidenceStatus.NON_EVIDENCE_SMOKE.value:
        raise ValueError("V1 smoke config evidence_status must be non_evidence_smoke")
    decision = validate_evidence_status(config["evidence_status"], mode=config["mode"])
    if not decision.passed:
        raise ValueError(decision.reason)
    if float(config["alpha"]) <= 0 or float(config["alpha"]) >= 1:
        raise ValueError("alpha must be between 0 and 1")
    if int(config["max_samples"]) <= 0:
        raise ValueError("max_samples must be positive")
    if not isinstance(config["metrics"], list) or not config["metrics"]:
        raise ValueError("metrics must be a non-empty list")
    return [
        f"project={config['project']}",
        f"version={config['version']}",
        f"mode={config['mode']}",
        f"metrics={','.join(str(item) for item in config['metrics'])}",
        f"evidence_status={config['evidence_status']}",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a CertGen config.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    summary = validate_config(config)
    print("CertGen config valid: " + "; ".join(summary))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
