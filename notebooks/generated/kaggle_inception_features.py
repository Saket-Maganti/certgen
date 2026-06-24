# CertGen V4 Feature Extraction Notebook Script
# Target: kaggle
# Feature extractor: inception_v3_pool3
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

FEATURE_EXTRACTOR = "inception_v3_pool3"
PREPROCESSING_LOCK_ID = "TBD"
EVIDENCE_STATUS = "real_unverified"
CLAIM_ALLOWED = False

print("This script writes feature caches and sidecars; validation is required before pilot use.")
print("Run certgen.cli.validate_feature_cache after extraction.")

# Real extraction code is intentionally user-run. No paid APIs or secrets are used.
