from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]


ROOT = Path(__file__).resolve().parents[2]


def test_report_producers_have_unique_canonical_roots() -> None:
    registry = yaml.safe_load((ROOT / "registry/icml2027/report_namespaces.yaml").read_text())
    rows = registry["namespaces"]
    producers = [row["producer_id"] for row in rows]
    roots = [row["canonical_root"].rstrip("/") for row in rows]
    assert len(producers) == len(set(producers))
    assert len(roots) == len(set(roots))
    for left_index, left in enumerate(roots):
        for right in roots[left_index + 1 :]:
            assert not left.startswith(right + "/")
            assert not right.startswith(left + "/")


def test_namespaces_are_non_evidence() -> None:
    registry = yaml.safe_load((ROOT / "registry/icml2027/report_namespaces.yaml").read_text())
    assert registry["claim_allowed"] is False
    report_copy = yaml.safe_load((ROOT / "reports/icml2027/REPORT_NAMESPACE_REGISTRY.yaml").read_text())
    assert report_copy["namespaces"]
    assert report_copy["claim_allowed"] is False
