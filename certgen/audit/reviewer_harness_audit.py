"""Audit V5 reviewer harness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.core.io import write_json
from certgen.review.reviewer_simulator import REQUIRED_ATTACKS, author_response_bank, reviewer_attack_bank, simulate_v5_scorecard


def audit_reviewer_harness() -> dict[str, Any]:
    errors: list[str] = []
    cards = reviewer_attack_bank()
    attacks = {card["attack"] for card in cards}
    for attack in REQUIRED_ATTACKS:
        if attack not in attacks:
            errors.append(f"missing attack: {attack}")
    for card in cards:
        response = card["response"].lower()
        if "%" in response or "we show" in response or "our results" in response:
            errors.append(f"{card['attack_id']}: response includes fake result language")
    fid_cards = [card for card in cards if "FID" in card["attack"]]
    if not fid_cards or "descriptive-only" not in fid_cards[0]["response"]:
        errors.append("FID attack response must mention descriptive-only policy")
    score = simulate_v5_scorecard(False)
    if score["empirical_strength"] != "blocked_until_real_runs":
        errors.append("no-results scorecard must block empirical strength")
    return {"passed": not errors, "errors": errors, "attacks": len(cards), "responses": len(author_response_bank()), "scorecard": score, "claim_allowed": False, "evidence_status": "template_only"}


def write_reviewer_harness_outputs(report: str | Path = "docs/review/REVIEWER_SCORE_SIMULATOR_V5.md", json_out: str | Path = "data/results/v5_reviewer_harness.json") -> dict[str, Any]:
    payload = audit_reviewer_harness()
    lines = ["# Reviewer Score Simulator V5", "", "`NO_REAL_EVIDENCE`", "", f"Passed: `{payload['passed']}`", f"Attacks: `{payload['attacks']}`", f"Empirical strength: `{payload['scorecard']['empirical_strength']}`"]
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload
