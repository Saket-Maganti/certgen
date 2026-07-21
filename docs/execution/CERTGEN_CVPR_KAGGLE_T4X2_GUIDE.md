# CertGen CVPR Kaggle T4x2 Guide

Create a private Kaggle dataset from the exact input ZIP; select two T4 GPUs; set internet only as required by verified model licenses/auth; confirm two visible devices; run all cells in order; preserve logs and the deterministic output ZIP. Single-GPU fallback is explicit and logged. Do not run certificates on Kaggle. Copy back without modifying the ZIP and import with `python3 -m certgen import <stage> <zip>`.
