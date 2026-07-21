#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 - <<'PY'
import json
import subprocess
from pathlib import Path

status = subprocess.run(["git", "status", "--short"], text=True, capture_output=True, check=False).stdout.splitlines()
prompt_packs = sorted(str(path) for path in Path(".").glob("certgen_prompt_pack_*"))
runbooks = sorted(str(path) for path in Path("docs").glob("V9_*.md"))
notebooks = sorted(str(path) for path in Path("notebooks/kaggle").glob("v9_*.ipynb"))
reports = sorted(str(path) for path in Path("data/results").glob("v9_*.json"))
payload = {
    "changed_files_count": len(status),
    "changed_files": status,
    "untracked_prompt_packs": prompt_packs,
    "generated_runbooks": runbooks,
    "generated_notebooks": notebooks,
    "generated_reports": reports,
    "candidate_archive_paths": ["data/kaggle_inputs", "data/kaggle_outputs", "data/imported"],
    "should_not_be_committed_as_evidence": ["data/kaggle_outputs/*", "data/imported/*", "run_log_only artifacts", "pilot_only artifacts"],
    "claim_allowed": False,
    "no_fake_results": True,
    "not_paper_evidence": True,
}
Path("data/results").mkdir(parents=True, exist_ok=True)
Path("data/results/v9_repo_snapshot_status.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
lines = [
    "# V9 Repo Snapshot and Worktree Status",
    "",
    "`NO_FAKE_RESULTS`",
    "`NO_REAL_EVIDENCE`",
    "`not paper evidence`",
    "",
    f"Changed files count: `{len(status)}`",
    "",
    "## Generated V9 Notebooks",
    *[f"- `{item}`" for item in notebooks or ["none"]],
    "",
    "## Generated V9 Reports",
    *[f"- `{item}`" for item in reports or ["none"]],
    "",
    "## Do Not Commit As Evidence",
    "- `data/kaggle_outputs/*`",
    "- `data/imported/*`",
    "- run-log-only artifacts",
    "- pilot-only artifacts",
    "",
    "No destructive changes were performed.",
]
Path("docs/V9_REPO_SNAPSHOT_AND_WORKTREE_STATUS.md").write_text("\n".join(lines) + "\n")
print(json.dumps(payload, indent=2, sort_keys=True))
PY
