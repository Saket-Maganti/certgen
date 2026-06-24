from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelRecord:
    model_id: str
    name: str
    family: str
    sample_source: str
    checkpoint_or_samples_available: bool
    license_note: str
    evidence_status: str
