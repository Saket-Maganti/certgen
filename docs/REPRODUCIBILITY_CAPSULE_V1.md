# Reproducibility Capsule V1

Environment assumptions:

- Python 3.10 or newer.
- CPU-local tests.
- No GPU requirement.
- No automatic large downloads.
- Heavy vision dependencies are optional and lazy.

CPU test command:

```bash
python -m pytest -q
```

Smoke regeneration:

```bash
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics --make-certificate
```

Future Kaggle or Colab feature extraction may be used for real feature caches, but it is outside V1 smoke tests.

Artifact directories:

- `data/smoke/v1`
- `data/results`
- `registry`

Every artifact must carry an evidence status.
