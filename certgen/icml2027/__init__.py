"""Prospective, non-claim ICML 2027 research infrastructure."""

from __future__ import annotations

SCHEMA_PREFIX = "certgen.icml2027"
TRUTH_BOUNDARY = {
    "synthetic_validation_only": True,
    "not_real_generator_evidence": True,
    "not_empirical_paper_evidence": True,
    "claim_allowed": False,
}
PLANNING_BOUNDARY = {"planning_only": True, "claim_allowed": False}
