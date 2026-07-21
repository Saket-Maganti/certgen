from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from certgen.packaging.kaggle_dataset_manifest import write_manifest


def prepare(folder: str | Path, *, dataset_name: str, source_zip: str | Path | None = None) -> dict[str, object]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if source_zip:
        source = Path(source_zip)
        if source.exists():
            shutil.copy2(source, folder / source.name)
    (folder / "README.md").write_text(
        f"# {dataset_name}\n\nUpload this folder as a Kaggle dataset. No secrets included.\n",
        encoding="utf-8",
    )
    payload = write_manifest(folder, dataset_name=dataset_name)
    (folder / "checksums.sha256").write_text(
        "\n".join(f"{item['sha256']}  {item['path']}" for item in payload["files"]) + "\n",
        encoding="utf-8",
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--source-zip", default=None)
    args = parser.parse_args(argv)
    print(json.dumps(prepare(args.folder, dataset_name=args.dataset_name, source_zip=args.source_zip), indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
