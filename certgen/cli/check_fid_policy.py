"""Check a certificate JSON for forbidden FID/FD rigorous claims."""

from __future__ import annotations

import argparse

from certgen.certs.fid_policy import assert_no_rigorous_fid_claim
from certgen.core.io import read_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check V2 FID/FD policy on a certificate JSON.")
    parser.add_argument("--certificate", required=True)
    args = parser.parse_args(argv)
    certificate = read_json(args.certificate)
    assert_no_rigorous_fid_claim(certificate)
    print(f"FID policy check passed: {args.certificate}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
