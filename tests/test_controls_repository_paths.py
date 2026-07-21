from pathlib import Path

from certgen.cvpr.controls import _source_path


def test_reference_manifest_repository_relative_path_resolves_from_project_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    (root / "certgen").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    manifest = root / "registry/manifests/cvpr/reference.jsonl"
    manifest.parent.mkdir(parents=True)
    image = root / "data/reference_materialized/image.ppm"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"P6\n1 1\n255\n\x00\x00\x00")

    resolved = _source_path({"path": "data/reference_materialized/image.ppm"}, manifest)

    assert resolved == image
