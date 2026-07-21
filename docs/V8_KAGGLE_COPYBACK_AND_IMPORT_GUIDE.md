# V8 Kaggle Copyback And Import Guide

Generation output:

```bash
bash commands/v8_cpu_execution/05_import_generation_zip_repair.sh /path/to/certgen_cifar10_generation_outputs.zip
```

Feature output:

```bash
bash commands/v8_cpu_execution/06_import_feature_zip_repair.sh /path/to/certgen_cifar10_features_outputs.zip
```

The current blocker remains `BLOCKED_MISSING_REFERENCE_SAMPLES` until a real CIFAR reference manifest/package exists. Do not treat notebook dry runs, preflight images, or planned manifests as paper evidence.
