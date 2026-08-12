"""One source-controlled worker subprocess for an authenticated notebook job."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.icml2027.common import write_json
from certgen.icml2027.notebook_runtime import _run_real_worker, _worker_spec, fixture_worker_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", required=True)
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--work-root", required=True)
    parser.add_argument("--job-index", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args(argv)
    if args.fixture:
        result = fixture_worker_result(args.lane, args.job_index)
    else:
        input_root = Path(args.input_root)
        spec = _worker_spec(input_root, args.lane)
        result = _run_real_worker(
            args.lane,
            spec,
            input_root,
            Path(args.work_root),
            job_index=args.job_index,
        )
    write_json(args.out, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
