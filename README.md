# CertGen

CertGen is an evaluation and audit framework for anytime-valid directional comparison under a fixed bounded-kernel protocol. The current claim-capable method is a disjoint-pair RBF-MMD difference stream with a conservative union-Hoeffding confidence sequence and Bonferroni family control. It is not metric-agnostic: FID/FD and polynomial KID remain descriptive.

Current status: `CVPR_RUN_READY_BLOCKED_ONLY_BY_REFERENCE_INPUT`.

There is no real CIFAR reference, checkpoint preflight, generated sample set, feature cache, metric reproduction, certificate, undecided fraction, or paper result in this repository. Smoke fixtures, simulations, notebooks, tests, and package manifests are not model evidence.

## Start here

```bash
python3 -m certgen status
python3 -m certgen next-action
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -m pytest -q -m 'not integration_audit'
```

To validate a user-supplied CIFAR-10 source without downloading anything:

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```

The canonical execution truth is in:

- `CERTGEN_CVPR_FINAL_RUN_READY_EXECUTION_HANDBOOK.md`
- `CERTGEN_CVPR_FINAL_RUN_READY_CLOSURE_REPORT.md`
- `docs/CERTGEN_CVPR_EXACT_NEXT_ACTION.md`
- `docs/CERTGEN_CVPR_SINGLE_FILE_HANDOFF.md`

Historical V1–V9 wrappers and reports are retained only for compatibility/context. They are not canonical guidance or evidence. Tests marked `integration_audit` intentionally launch a fresh default non-integration test subprocess and must be run explicitly with `python3 -m pytest -q -m integration_audit`.
