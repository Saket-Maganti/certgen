"""Reviewer attack cards for V4."""

ATTACKS = [
    "This is just KID with error bars.",
    "Anytime-valid inference is known; what is new?",
    "FID is nonlinear, so your certificate is invalid.",
    "This is a statistics paper, not CVPR.",
    "No new metric.",
    "Only toy datasets.",
    "Published metric gaps are already known to be noisy.",
    "You selected only small gaps to make papers look bad.",
    "Preprocessing mismatch invalidates your audit.",
    "Multiple comparisons inflate false discoveries.",
    "Reference samples are reused; independence is violated.",
    "Video extension is too shallow.",
    "Zero-cost constraint limits scope too much.",
    "No human preference validation.",
    "The tool does not change conclusions.",
]


def attack_cards() -> list[dict]:
    cards = []
    for idx, attack in enumerate(ATTACKS, start=1):
        blocker = idx in {1, 3, 4, 9, 10, 11}
        cards.append(
            {
                "attack_id": f"A{idx:02d}",
                "attack": attack,
                "severity": "high" if blocker else "medium",
                "likelihood": "high" if idx <= 5 else "medium",
                "evidence_needed": "real pilot evidence and audit gates" if blocker else "clear writing and limitations",
                "required_artifact": "V5 real pilot" if blocker else "V4 docs",
                "current_status": "blocked_before_real_evidence" if blocker else "draft_response_available",
                "response_draft": "CertGen is a decision layer and audit pipeline; claims remain blocked until evidence gates pass.",
                "blocker": blocker,
            }
        )
    return cards
