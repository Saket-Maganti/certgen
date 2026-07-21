# Canonical Prepare Commands

Run preparation locally from the repository root. Builders derive values from registries and validated prior imports; unresolved values and unknown licenses block instead of producing runnable YAML.

```bash
python3 -m certgen prepare preflight --asset-policy ONLINE_PREFLIGHT_DOWNLOAD --license-approvals <approved-license-map.json>
python3 -m certgen prepare generation --scale 1k
python3 -m certgen prepare features
python3 -m certgen prepare family
python3 -m certgen prepare runtime-plan --config <frozen-runtime-plan.yaml> --out <runtime-plan.json> --ingest-preflight <measured-preflight.json>
```

The preflight builder selects registered CIFAR models and asset requirements. Generation binds the validated preflight import, 10,000-row reference manifest, model revisions, deterministic seeds/shards and configuration hashes. Feature preparation binds the imported generation and exact observed preprocessing contracts. Family preparation freezes the prospective comparison family and Bonferroni allocation.
