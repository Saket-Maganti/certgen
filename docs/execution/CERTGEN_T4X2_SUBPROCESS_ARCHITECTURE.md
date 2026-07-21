# T4x2 Subprocess Architecture

The notebook parent never imports PyTorch or initializes CUDA. It may call `nvidia-smi` to confirm the requested devices, then starts independent `python -m certgen.notebooks.workers.<worker>` subprocesses. Each child receives one `CUDA_VISIBLE_DEVICES` value in its environment before the first lazy PyTorch import and records logical/physical device assignment, torch/CUDA versions, GPU name, memory and configuration identity.

The orchestrator preserves per-worker stdout/stderr logs, status paths, exit codes, timeouts, rerun commands and resume markers. One failed child yields `PARTIAL_FAILURE`; it never becomes wrapper success. Single-GPU fallback is forbidden unless the frozen config explicitly enables and records it.
