"""Report renderer for the synthetic optional-stopping lab."""

from __future__ import annotations


def render_optional_stopping_report(summary: dict) -> str:
    lines = [
        "# V2 Optional-Stopping Lab",
        "",
        "`SMOKE_SIMULATION_ONLY_NOT_REAL_EVIDENCE`",
        "",
        "This synthetic smoke simulation is not a benchmark result.",
        "In synthetic smoke simulations, the monitoring path behaves as expected.",
        "",
        f"- Evidence status: `{summary['evidence_status']}`",
        f"- Replicates: `{summary['num_replicates']}`",
        f"- Budget: `{summary['budget']}`",
        f"- Alpha: `{summary['alpha']}`",
        "",
    ]
    for scenario, methods in summary["scenarios"].items():
        lines.extend([f"## {scenario}", "", "| Method | Decision Rate | False-Decision Rate | Avg Units |", "|---|---:|---:|---:|"])
        for method, stats in methods.items():
            avg = stats["average_sample_units_to_decision"]
            avg_text = "NA" if avg is None else f"{avg:.2f}"
            lines.append(
                f"| `{method}` | {stats['decision_rate']:.3f} | {stats['false_decision_rate']:.3f} | {avg_text} |"
            )
        lines.append("")
    return "\n".join(lines)
