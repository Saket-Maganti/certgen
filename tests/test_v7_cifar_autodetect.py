from __future__ import annotations

from pathlib import Path

from certgen.data.autodetect_cifar10_root import detect_cifar10_root


def test_detect_official_batch_like_fixture(tmp_path: Path) -> None:
    root = tmp_path / "cifar-10-batches-py"
    root.mkdir()
    for idx in range(1, 6):
        (root / f"data_batch_{idx}").write_bytes(b"fixture")
    detection = detect_cifar10_root(tmp_path)
    assert detection.status == "ready"
    assert detection.layout == "official_cifar_10_batches_py"
    assert detection.claim_allowed is False


def test_detect_image_folder_fixture(tmp_path: Path) -> None:
    for name in ["cat", "dog"]:
        folder = tmp_path / name
        folder.mkdir()
        (folder / "sample.png").write_bytes(b"fixture")
    detection = detect_cifar10_root(tmp_path)
    assert detection.status == "ready"
    assert detection.layout == "image_folder_class_tree"


def test_detect_unsupported_layout(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("not cifar", encoding="utf-8")
    detection = detect_cifar10_root(tmp_path)
    assert detection.status == "blocked"
    assert detection.blocker_code == "BLOCKED_MISSING_REFERENCE_SAMPLES"
