"""Paper-facing table specs."""

def table_specs() -> list[dict]:
    names = ["main_audit_table", "metric_reproduction_table", "sample_availability_table", "certificate_summary_table", "ranking_stability_table", "limitations_table"]
    return [{"table_id": name, "watermark": "NON-EVIDENCE / TEMPLATE / SYNTHETIC", "claim_allowed": False} for name in names]
