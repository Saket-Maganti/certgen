"""Canonical CVPR pre-execution contracts for CertGen.

This package contains protocol and execution infrastructure only.  It never
promotes an artifact to paper evidence and all generated records default to
``claim_allowed=False``.
"""

from certgen.cvpr.contracts import CVPRStage, EvidenceClass, StageTransition

__all__ = ["CVPRStage", "EvidenceClass", "StageTransition"]
