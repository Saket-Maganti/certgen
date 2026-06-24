from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DatasetRecord:
    dataset_id: str
    name: str
    split: str
    source_url_or_note: str
    license_note: str
    num_items_declared: int | None
    evidence_status: str
    provenance_hash: str
