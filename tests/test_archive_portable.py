"""Minimal non-Git checks that must pass inside a clean release archive."""

from pathlib import Path


def test_archive_portable_imports_and_notebook_paths() -> None:
    import certgen
    from certgen.cvpr.output_schemas import OUTPUT_SCHEMAS
    from certgen.notebooks.cvpr_factory import NOTEBOOK_SPECS

    assert certgen.__version__
    assert all(Path(path).is_file() for path in NOTEBOOK_SPECS)
    assert set(OUTPUT_SCHEMAS) == {"preflight", "generation", "feature"}
    for required in (
        "LICENSE",
        "CITATION.cff",
        "CERTGEN_CVPR_REAL_EXECUTION_CLOSURE_REPORT.md",
        "CERTGEN_CVPR_RUN_READY_EXECUTION_HANDBOOK.md",
        "reports/CERTGEN_REAL_EXECUTION_CLOSURE_CURRENT_STATE.json",
    ):
        assert Path(required).is_file()
