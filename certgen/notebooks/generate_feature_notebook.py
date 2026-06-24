"""Generate safe feature-extraction notebook scripts."""

from __future__ import annotations

from pathlib import Path

from certgen.core.io import read_json


def generate_feature_notebook(plan_path: str | Path, target: str, feature_extractor: str, out: str | Path) -> str:
    plan = read_json(plan_path)
    script = f'''# CertGen V4 Feature Extraction Notebook Script
# Target: {target}
# Feature extractor: {feature_extractor}
# NO_REAL_EVIDENCE

import os
from pathlib import Path

SAMPLE_MANIFEST = os.environ.get("CERTGEN_SAMPLE_MANIFEST", "")
OUTPUT_DIR = Path(os.environ.get("CERTGEN_FEATURE_OUT_DIR", "data/features/manual_run"))
ALLOW_DOWNLOADS = os.environ.get("CERTGEN_ALLOW_LARGE_DOWNLOADS", "0") == "1"

if not SAMPLE_MANIFEST:
    raise SystemExit("Set CERTGEN_SAMPLE_MANIFEST to a user-provided sample manifest.")
if not ALLOW_DOWNLOADS:
    print("Large downloads are disabled. Provide local/released samples manually.")

FEATURE_EXTRACTOR = "{feature_extractor}"
PREPROCESSING_LOCK_ID = "{plan.get('preprocessing_lock_id') or 'unknown'}"
EVIDENCE_STATUS = "real_unverified"
CLAIM_ALLOWED = False

print("This script writes feature caches and sidecars; validation is required before pilot use.")
print("Run certgen.cli.validate_feature_cache after extraction.")

# Real extraction code is intentionally user-run. No paid APIs or secrets are used.
'''
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(script, encoding="utf-8")
    return script
