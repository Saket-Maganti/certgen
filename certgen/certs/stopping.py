"""Stopping-rule helpers."""

from __future__ import annotations

from certgen.core.enums import CertificateStatus


def status_from_interval(lower: float, upper: float) -> str:
    if upper < 0:
        return CertificateStatus.CERTIFIED_A_BETTER.value
    if lower > 0:
        return CertificateStatus.CERTIFIED_B_BETTER.value
    return CertificateStatus.NOT_DECIDED_AT_BUDGET.value
