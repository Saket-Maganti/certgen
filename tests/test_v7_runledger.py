from __future__ import annotations

import pytest

from certgen.runledger.ledger import LedgerEvent, append_event, current_blocker, read_events


def test_ledger_event_rejects_claim_allowed_true() -> None:
    with pytest.raises(ValueError):
        LedgerEvent(
            stage="bad",
            command="none",
            status="bad",
            claim_allowed=True,
        ).to_json()


def test_ledger_stage_transition(tmp_path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    append_event(
        ledger,
        LedgerEvent(
            stage="reference",
            command="detect",
            status="blocked",
            blocker_code="BLOCKED_MISSING_REFERENCE_SAMPLES",
        ),
    )
    events = read_events(ledger)
    assert current_blocker(events) == "BLOCKED_MISSING_REFERENCE_SAMPLES"
    assert events[0]["claim_allowed"] is False
