from __future__ import annotations

import json
from pathlib import Path

from certgen.generation.checkpoint_adapters import CHECKPOINT_IDS, preflight_checkpoint
from certgen.notebooks.validate_kaggle_notebooks import validate_notebook


def test_notebook_validator_accepts_required_strings(tmp_path: Path) -> None:
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "claim_allowed=false run_log_only RESUME generation_status.json "
                    "output ZIP copy-back"
                ],
            }
        ],
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = tmp_path / "bookrun.ipynb"
    path.write_text(json.dumps(nb), encoding="utf-8")
    assert validate_notebook(path)["ok"] is True


def test_checkpoint_preflight_is_planned_only_without_download() -> None:
    payload = preflight_checkpoint(CHECKPOINT_IDS[0], allow_download=False)
    assert payload.claim_allowed is False
    assert payload.status == "planned_only"
