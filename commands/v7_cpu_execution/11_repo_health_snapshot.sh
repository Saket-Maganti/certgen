#!/usr/bin/env bash
set -euo pipefail
find . -maxdepth 2 -type f | wc -l && git status --short || true
