"""Claim-language scanner for non-evidence reports."""

from __future__ import annotations

from dataclasses import dataclass

from certgen.core.enums import NON_EVIDENCE_STATUSES, normalize_enum_value


FORBIDDEN_PHRASES = [
    "we find that",
    "we show that",
    "certified result",
    "paper evidence",
    "real evidence",
    "model a beats model b",
    "published wins are undecided",
    "ranking changes",
    "compute saving",
    "empirical result",
    "fid-certified winner",
    "anytime-valid fid result",
    "rigorous fid certificate",
    "fid proves a beats b",
    "our results demonstrate",
    "model a is better",
    "% of claims fail",
]

ALLOWED_CAUTIOUS_PHRASES = [
    "smoke artifact",
    "non-evidence",
    "planned",
    "placeholder",
    "toy",
    "contract validation",
]


@dataclass
class ClaimGateDecision:
    passed: bool
    violations: list[str]

    @property
    def reason(self) -> str:
        if self.passed:
            return "claim gate passed"
        return "forbidden claim language: " + ", ".join(self.violations)


def scan_text_for_forbidden_claims(text: str, *, evidence_status: str = "non_evidence_smoke") -> ClaimGateDecision:
    status = normalize_enum_value(evidence_status)
    if status not in NON_EVIDENCE_STATUSES:
        return ClaimGateDecision(True, [])
    lowered = text.lower()
    # V2 reports intentionally use these negated safety labels.
    lowered = lowered.replace("not paper evidence", "")
    lowered = lowered.replace("no real evidence", "")
    violations = [phrase for phrase in FORBIDDEN_PHRASES if phrase in lowered]
    return ClaimGateDecision(not violations, violations)


def assert_claim_safe(text: str, *, evidence_status: str = "non_evidence_smoke") -> None:
    decision = scan_text_for_forbidden_claims(text, evidence_status=evidence_status)
    if not decision.passed:
        raise ValueError(decision.reason)


def scan_report_for_overclaims(text: str, *, claim_allowed: bool) -> ClaimGateDecision:
    if claim_allowed:
        return ClaimGateDecision(True, [])
    lowered = text.lower()
    lowered = lowered.replace("not paper evidence", "")
    lowered = lowered.replace("no_real_validated_features", "")
    lowered = lowered.replace("real_features_used_in_non_claim_mode", "")
    lowered = lowered.replace("computed in non-claim mode", "")
    lowered = lowered.replace("pilot diagnostic", "")
    lowered = lowered.replace("claim blocked", "")
    violations = []
    for phrase in [
        "we show that",
        "our results demonstrate",
        "model a is better",
        "published wins are undecided",
        "% of claims fail",
        "ranking changes",
    ]:
        if phrase in lowered:
            violations.append(phrase)
    if "statistically decided" in lowered and "non-claim" not in lowered and "smoke" not in lowered:
        violations.append("statistically decided")
    return ClaimGateDecision(not violations, violations)
