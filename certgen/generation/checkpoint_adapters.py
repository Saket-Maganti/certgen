"""Checkpoint adapter preflight metadata for V7 Kaggle generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass


CHECKPOINT_IDS = (
    "google/ddpm-cifar10-32",
    "FrankCCCCC/ddpm_ema_cifar10",
    "FrankCCCCC/cfm-cifar10-32",
)


@dataclass(frozen=True)
class CheckpointPreflight:
    checkpoint_id: str
    status: str
    blocker_code: str | None
    retryable: bool
    claim_allowed: bool = False
    evidence_status: str = "run_log_only"

    def asdict(self) -> dict[str, object]:
        return asdict(self)


def preflight_checkpoint(checkpoint_id: str, *, allow_download: bool = False) -> CheckpointPreflight:
    if checkpoint_id not in CHECKPOINT_IDS:
        return CheckpointPreflight(
            checkpoint_id,
            "blocked",
            "BLOCKED_UNKNOWN_CHECKPOINT",
            retryable=False,
        )
    if not allow_download:
        return CheckpointPreflight(
            checkpoint_id,
            "planned_only",
            "RUN_ON_KAGGLE_WITH_MODEL_ACCESS",
            retryable=True,
        )
    return CheckpointPreflight(checkpoint_id, "ready_for_kaggle_load_check", None, retryable=True)
