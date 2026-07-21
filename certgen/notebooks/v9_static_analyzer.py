"""Static analyzer for V9 Kaggle notebooks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from certgen.core.io import write_json


NOTEBOOKS = [
    "notebooks/kaggle/v9_checkpoint_real_load_preflight_t4x2.ipynb",
    "notebooks/kaggle/v9_cifar10_generation_t4x2_1k_hardened.ipynb",
    "notebooks/kaggle/v9_cifar10_feature_extraction_t4x2_1k_hardened.ipynb",
]
SECRET_PATTERNS = [re.compile(r"sk-[A-Za-z0-9]{20,}"), re.compile(r"ghp_[A-Za-z0-9]{20,}")]
CLAIM_KEY = "claim_allowed"
CLAIM_EQUALS_TRUE = f"{CLAIM_KEY}=true"
CLAIM_JSON_TRUE = f'"{CLAIM_KEY}": true'


def notebook_text(path: str | Path) -> str:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return "\n".join("".join(cell.get("source", [])) for cell in data.get("cells", []))


def _stored_output_issues(data: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for index, cell in enumerate(data.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            issues.append(f"stored output in code cell {index}")
        if cell.get("execution_count") is not None:
            issues.append(f"execution_count retained in code cell {index}")
    return issues


def analyze_notebook(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"path": str(path), "passed": False, "missing": ["notebook missing"], "forbidden": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    text = notebook_text(path)
    lowered = text.lower()
    required = {
        "t4x2_gpu_check": "torch.cuda.device_count() < 2" in text and "get_device_name" in text,
        "output_zip_creation": ".zip" in text and ("zip -qr" in text or "zipfile" in text),
        "blocked_status_json": "blocked_status.json" in text or "BLOCKED_" in text,
        "no_paper_evidence_text": "not paper evidence" in text,
        "resume_logic": "resume" in text.lower() or "RESUME" in text,
        "runtime_logging": "wall_time" in text or "time.time()" in text,
        "copy_back_instructions": "copy back" in text.lower() or "Copy back" in text,
        "pinned_dependencies": "==" in text and "pip freeze" in lowered,
        "integrity_manifest": "output_zip_integrity_manifest.json" in text,
        "non_destructive_output": "refusing to overwrite" in lowered,
        "no_stored_outputs": not _stored_output_issues(data),
    }
    name = path.name
    if "generation" in name:
        required.update(
            {
                "revision_locks": len(set(re.findall(r"[0-9a-f]{40}", lowered))) >= 3,
                "mandatory_preflight": "BLOCKED_PREFLIGHT_MISSING" in text and "mandatory checkpoint preflight" in lowered,
                "actual_two_gpu_concurrency": "ThreadPoolExecutor(max_workers=2)" in text and "pool.submit(run_shard" in text,
                "safe_input_zip": "archive.testzip()" in text and "unsafe input ZIP member" in text and "unzip -q -o" not in text,
                "validated_resume": "manifest_is_complete" in text and "image_hash" in text,
                "atomic_shard_status": "os.replace(temporary,status)" in text,
            }
        )
    elif "feature_extraction" in name:
        required.update(
            {
                "extractor_revision_locks": "32bd64288804d66eefd0ccbe215aa642df71cc41" in lowered and "inception_v3_weights.imagenet1k_v1" in lowered,
                "actual_two_gpu_concurrency": "ThreadPoolExecutor(max_workers=2)" in text and "pool.submit(run_extractor_shard" in text,
                "safe_input_zip": "archive.testzip()" in text and "unsafe input ZIP member" in text and "unzip -q -o" not in text,
                "validated_resume": "shard_cache_valid" in text and "np.isfinite" in text,
                "atomic_shard_status": "os.replace(temporary,status_path)" in text,
            }
        )
    else:
        required["revision_locks"] = len(set(re.findall(r"[0-9a-f]{40}", lowered))) >= 3
    forbidden = []
    for needle in [
        "certify_clean_metric",
        "run_batch_certificates",
        CLAIM_EQUALS_TRUE,
        CLAIM_JSON_TRUE,
        "paper evidence generation",
        "|| true",
        "extractall(",
        "previous preflight outputs may be overwritten",
    ]:
        if needle in text:
            forbidden.append(needle)
    forbidden.extend(_stored_output_issues(data))
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            forbidden.append(pattern.pattern)
    missing = [key for key, ok in required.items() if not ok]
    return {"path": str(path), "passed": not missing and not forbidden, "missing": missing, "forbidden": forbidden}


def run_analysis(notebooks: list[str] | None = None, out_json: str | Path = "data/results/v9_notebook_static_analysis.json", out_report: str | Path = "docs/V9_NOTEBOOK_STATIC_ANALYSIS.md") -> dict[str, Any]:
    paths = notebooks or NOTEBOOKS
    results = [analyze_notebook(path) for path in paths]
    payload = {
        "passed": all(item["passed"] for item in results),
        "results": results,
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    write_json(payload, out_json)
    lines = [
        "# V9 Notebook Static Analysis",
        "",
        "`NO_FAKE_RESULTS`",
        "`NO_REAL_EVIDENCE`",
        "`not paper evidence`",
        "",
        f"Passed: `{payload['passed']}`",
        "",
        "| Notebook | Passed | Missing | Forbidden |",
        "|---|---:|---|---|",
    ]
    for item in results:
        lines.append(f"| `{item['path']}` | `{item['passed']}` | `{', '.join(item['missing']) or 'none'}` | `{', '.join(item['forbidden']) or 'none'}` |")
    Path(out_report).parent.mkdir(parents=True, exist_ok=True)
    Path(out_report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebooks", nargs="*")
    parser.add_argument("--out-json", default="data/results/v9_notebook_static_analysis.json")
    parser.add_argument("--out-report", default="docs/V9_NOTEBOOK_STATIC_ANALYSIS.md")
    args = parser.parse_args(argv)
    payload = run_analysis(args.notebooks or None, args.out_json, args.out_report)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
