"""Generate safe V5 command bundle scripts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


COMMANDS: list[tuple[str, str]] = [
    ("00_validate_state.sh", "python3 -m certgen.audit.v5_state_intake --out docs/V5_STATE_INTAKE.md --json-out data/results/v5_state_intake.json"),
    ("01_validate_provenance_ledger.sh", ": \"${CERTGEN_LEDGER:?set CERTGEN_LEDGER to a real provenance ledger}\"\npython3 -m certgen.cli.validate_provenance_ledger --ledger \"$CERTGEN_LEDGER\" --out docs/PROVENANCE_LEDGER_VALIDATION.md --json-out data/results/provenance_ledger_validation.json --allow-missing-local"),
    ("02_validate_or_materialize_feature_caches.sh", ": \"${CERTGEN_FEATURES:?set CERTGEN_FEATURES to an .npz feature cache}\"\n: \"${CERTGEN_SIDECAR:?set CERTGEN_SIDECAR to the matching sidecar}\"\npython3 -m certgen.cli.validate_feature_cache --features \"$CERTGEN_FEATURES\" --sidecar \"$CERTGEN_SIDECAR\" --out docs/FEATURE_CACHE_VALIDATION.md --json-out data/results/feature_cache_validation.json --strict-hash"),
    ("03_reproduce_metric_point_estimate.sh", ": \"${CERTGEN_METRIC_REPRO_CONFIG:?set CERTGEN_METRIC_REPRO_CONFIG}\"\npython3 -m certgen.cli.audit_metric_reproduction --config \"$CERTGEN_METRIC_REPRO_CONFIG\" --out docs/METRIC_REPRODUCTION_AUDIT.md --json-out data/results/metric_reproduction_audit.json"),
    ("04_run_first_clean_core_pilot_nonclaim.sh", ": \"${CERTGEN_PILOT_CONFIG:?set CERTGEN_PILOT_CONFIG}\"\npython3 -m certgen.cli.run_first_pilot --pilot-config \"$CERTGEN_PILOT_CONFIG\" --out-dir data/results/first_real_clean_core_pilot --report docs/FIRST_REAL_CLEAN_CORE_PILOT_REPORT.md --json-out data/results/first_real_clean_core_pilot/summary.json"),
    ("05_render_pilot_report_card_nonclaim.sh", ": \"${CERTGEN_PILOT_SUMMARY:?set CERTGEN_PILOT_SUMMARY}\"\npython3 -m certgen.cli.render_pilot_report --summary-json \"$CERTGEN_PILOT_SUMMARY\" --out docs/FIRST_REAL_CLEAN_CORE_PILOT_REPORT.md"),
    ("06_v5_final_audit.sh", "python3 -m certgen.audit.v5_audit --out docs/V5_FINAL_AUDIT.md --json-out data/results/v5_final_audit.json"),
]


def generate_v5_command_bundle(out_dir: str | Path = "commands/v5") -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, body in COMMANDS:
        path = out_dir / name
        text = "#!/usr/bin/env bash\nset -euo pipefail\n\n# V5 safe command bundle. Defaults are validation/non-claim only.\n" + body + "\n"
        path.write_text(text, encoding="utf-8")
        path.chmod(path.stat().st_mode | 0o111)
        written.append(str(path))
    return {"scripts": written, "claim_allowed": False, "evidence_status": "dry_run_only"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate V5 command bundle.")
    parser.add_argument("--out-dir", default="commands/v5")
    args = parser.parse_args(argv)
    payload = generate_v5_command_bundle(args.out_dir)
    print(f"Wrote {len(payload['scripts'])} V5 command scripts to {args.out_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
