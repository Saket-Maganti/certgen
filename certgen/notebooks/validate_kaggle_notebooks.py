from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_STRINGS = [
    "claim_allowed=false",
    "run_log_only",
    "RESUME",
    "generation_status.json",
    "output ZIP",
    "copy-back",
]


def validate_notebook(path: str | Path) -> dict[str, object]:
    path = Path(path)
    nb = json.loads(path.read_text(encoding="utf-8"))
    text = "\n".join(
        "".join(cell.get("source", [])) for cell in nb.get("cells", []) if cell.get("cell_type")
    )
    missing = [needle for needle in REQUIRED_STRINGS if needle not in text]
    forbidden = [
        needle
        for needle in ["claim_allowed=true", "certify_clean_metric", "run_batch_certificates"]
        if needle in text
    ]
    return {"path": str(path), "missing": missing, "forbidden": forbidden, "ok": not missing and not forbidden}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebooks", nargs="+")
    parser.add_argument("--out", default="data/results/v7_notebook_quality.json")
    args = parser.parse_args(argv)
    results = [validate_notebook(path) for path in args.notebooks]
    payload = {"results": results, "ok": all(result["ok"] for result in results)}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
