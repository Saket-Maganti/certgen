"""Canonical, portable image-manifest contract shared by generation and features."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from PIL import Image

from certgen.core.hashing import file_sha256


SCHEMA_VERSION = "certgen.cvpr.image_manifest.v1"
REQUIRED_FIELDS = {
    "sample_id",
    "role",
    "model_id",
    "relative_image_path",
    "image_hash",
    "seed",
    "prompt_or_class_id",
    "width",
    "height",
    "mode",
    "source_run_id",
    "source_manifest_hash",
}
CONTROL_LINEAGE_FIELDS = (
    "source_id",
    "source_role",
    "clean_or_corrupted",
    "corruption_type",
    "corruption_severity",
    "corruption_seed",
    "reference_draw_id",
    "study_hash",
    "preprocessing_hash",
)
LEGACY_PATH_FIELDS = {"path", "image_path", "source_path", "sha256"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_MODES = {"RGB", "RGBA", "L"}
ALLOWED_ROLES = {
    "reference",
    "model",
    "control_null_a",
    "control_null_b",
    "control_obvious_clean",
    "control_obvious_corrupted",
}


def role_id_for_row(row: Mapping[str, Any]) -> str:
    role = str(row["role"])
    model_id = str(row["model_id"])
    if role == "reference":
        return "reference"
    if role == "model":
        return f"model__{model_id}"
    if role in ALLOWED_ROLES:
        return f"control__{model_id}"
    raise ValueError(f"unsupported canonical image role: {role}")


def safe_relative_image_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or not path.parts
        or ".." in path.parts
        or "\\" in value
        or any(part in {"", "."} for part in path.parts)
    ):
        raise ValueError(f"unsafe relative_image_path: {value!r}")
    return path


@dataclass(frozen=True)
class ImageManifestRow:
    sample_id: str
    role: str
    model_id: str
    relative_image_path: str
    image_hash: str
    seed: int | None
    prompt_or_class_id: str | int | None
    width: int
    height: int
    mode: str
    source_run_id: str
    source_manifest_hash: str
    source_id: str | int | None = None
    source_role: str | None = None
    clean_or_corrupted: str | None = None
    corruption_type: str | None = None
    corruption_severity: float | None = None
    corruption_seed: int | None = None
    reference_draw_id: str | int | None = None
    study_hash: str | None = None
    preprocessing_hash: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_row(raw: ImageManifestRow | Mapping[str, Any]) -> dict[str, Any]:
    row = raw.as_dict() if isinstance(raw, ImageManifestRow) else dict(raw)
    missing = sorted(REQUIRED_FIELDS - set(row))
    if missing:
        raise ValueError("image manifest row missing fields: " + ", ".join(missing))
    legacy = sorted(LEGACY_PATH_FIELDS & set(row))
    if legacy:
        raise ValueError("new image manifests must not contain legacy fields: " + ", ".join(legacy))
    for field in ("sample_id", "model_id", "source_run_id"):
        value = str(row[field])
        if not SAFE_ID.fullmatch(value):
            raise ValueError(f"{field} is empty or path-unsafe: {value!r}")
        row[field] = value
    if row["role"] not in ALLOWED_ROLES:
        raise ValueError("unsupported canonical image role")
    if row["role"] == "reference" and row["model_id"] != "reference":
        raise ValueError("reference rows must use model_id=reference")
    if row["role"] == "model" and row["model_id"] == "reference":
        raise ValueError("model rows require a non-reference model_id")
    if str(row["role"]).startswith("control_") and row["model_id"] == "reference":
        raise ValueError("control rows require an explicit frozen control model_id")
    is_control = str(row["role"]).startswith("control_")
    if is_control:
        missing_lineage = sorted(field for field in CONTROL_LINEAGE_FIELDS if field not in row)
        if missing_lineage:
            raise ValueError("control image row missing lineage fields: " + ", ".join(missing_lineage))
        for field in ("source_id", "reference_draw_id"):
            value = row[field]
            if value is None or isinstance(value, bool) or not isinstance(value, (str, int)):
                raise ValueError(f"{field} must be a nonempty string or integer for controls")
            if isinstance(value, str) and not value:
                raise ValueError(f"{field} must be a nonempty string or integer for controls")
        if not isinstance(row["source_role"], str) or not row["source_role"]:
            raise ValueError("source_role must be nonempty for controls")
        if row["clean_or_corrupted"] not in {"clean", "corrupted"}:
            raise ValueError("clean_or_corrupted must be clean or corrupted for controls")
        if not isinstance(row["corruption_type"], str) or not row["corruption_type"]:
            raise ValueError("corruption_type must be nonempty for controls")
        severity = row["corruption_severity"]
        if isinstance(severity, bool) or not isinstance(severity, (int, float)) or severity < 0:
            raise ValueError("corruption_severity must be a nonnegative number for controls")
        corruption_seed = row["corruption_seed"]
        if not isinstance(corruption_seed, int) or isinstance(corruption_seed, bool) or corruption_seed < 0:
            raise ValueError("corruption_seed must be a nonnegative integer for controls")
        for field in ("study_hash", "preprocessing_hash"):
            value = str(row[field]).lower()
            if not SHA256.fullmatch(value):
                raise ValueError(f"{field} must be a lowercase SHA-256 for controls")
            row[field] = value
    row["relative_image_path"] = safe_relative_image_path(str(row["relative_image_path"])).as_posix()
    digest = str(row["image_hash"]).lower()
    if not SHA256.fullmatch(digest):
        raise ValueError("image_hash must be a lowercase SHA-256")
    row["image_hash"] = digest
    lineage_hash = str(row["source_manifest_hash"]).lower()
    if not SHA256.fullmatch(lineage_hash):
        raise ValueError("source_manifest_hash must be a lowercase SHA-256")
    row["source_manifest_hash"] = lineage_hash
    seed = row["seed"]
    if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool) or seed < 0):
        raise ValueError("seed must be a nonnegative integer or null")
    prompt = row["prompt_or_class_id"]
    if prompt is not None and (isinstance(prompt, bool) or not isinstance(prompt, (str, int))):
        raise ValueError("prompt_or_class_id must be a string, integer, or null")
    for field in ("width", "height"):
        value = row[field]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{field} must be a positive integer")
    if row["mode"] not in ALLOWED_MODES:
        raise ValueError(f"unsupported image mode: {row['mode']}")
    fields = tuple(REQUIRED_FIELDS)
    ordered_fields = tuple(
        field for field in ImageManifestRow.__dataclass_fields__ if field in REQUIRED_FIELDS
    )
    if set(ordered_fields) != set(fields):  # pragma: no cover - import-time contract guard
        raise RuntimeError("image manifest dataclass and required fields disagree")
    if is_control:
        ordered_fields += CONTROL_LINEAGE_FIELDS
    return {field: row[field] for field in ordered_fields}


def validate_rows(
    rows: Iterable[ImageManifestRow | Mapping[str, Any]],
    *,
    root: str | Path | None = None,
    decode: bool = True,
) -> list[dict[str, Any]]:
    normalized = [normalize_row(row) for row in rows]
    if not normalized:
        raise ValueError("image manifest must contain at least one row")
    sample_ids = [row["sample_id"] for row in normalized]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("image manifest sample_id values must be unique")
    relative_paths = [row["relative_image_path"] for row in normalized]
    if len(relative_paths) != len(set(relative_paths)):
        raise ValueError("image manifest relative_image_path values must be unique")
    if root is not None:
        base = Path(root).resolve()
        for row in normalized:
            path = base.joinpath(*PurePosixPath(row["relative_image_path"]).parts)
            try:
                path.resolve().relative_to(base)
            except ValueError as exc:  # pragma: no cover - safe_relative_image_path already guards this
                raise ValueError("resolved image path escapes the declared root") from exc
            if not path.is_file():
                raise FileNotFoundError(f"image manifest path is unavailable: {row['relative_image_path']}")
            if file_sha256(path) != row["image_hash"]:
                raise ValueError(f"image hash mismatch: {row['relative_image_path']}")
            if decode:
                with Image.open(path) as image:
                    image.load()
                    if image.size != (row["width"], row["height"]) or image.mode != row["mode"]:
                        raise ValueError(f"decoded image contract mismatch: {row['relative_image_path']}")
    return normalized


def read_image_manifest(
    path: str | Path,
    *,
    root: str | Path | None = None,
    decode: bool = True,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid image manifest JSON on line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"image manifest line {line_number} must be an object")
        rows.append(value)
    return validate_rows(rows, root=root, decode=decode)


def write_image_manifest(
    rows: Iterable[ImageManifestRow | Mapping[str, Any]],
    path: str | Path,
    *,
    root: str | Path | None = None,
    decode: bool = True,
) -> list[dict[str, Any]]:
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite image manifest: {output}")
    normalized = validate_rows(rows, root=root, decode=decode)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in normalized),
        encoding="utf-8",
    )
    temporary.replace(output)
    return normalized


def migrate_legacy_row(
    raw: Mapping[str, Any],
    *,
    role: str,
    model_id: str,
    relative_image_path: str,
    source_run_id: str,
    source_manifest_hash: str,
) -> dict[str, Any]:
    """Explicit historical migration helper; canonical writers must not call it implicitly."""

    return normalize_row(
        {
            "sample_id": str(raw["sample_id"]),
            "role": role,
            "model_id": model_id,
            "relative_image_path": relative_image_path,
            "image_hash": raw.get("image_hash") or raw.get("sha256"),
            "seed": raw.get("seed"),
            "prompt_or_class_id": raw.get("prompt_or_class_id") or raw.get("prompt") or raw.get("class_id"),
            "width": raw["width"],
            "height": raw["height"],
            "mode": raw.get("mode", "RGB"),
            "source_run_id": source_run_id,
            "source_manifest_hash": source_manifest_hash,
        }
    )


def manifest_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = validate_rows(rows, decode=False)
    counts: dict[str, int] = {}
    for row in normalized:
        key = role_id_for_row(row)
        counts[key] = counts.get(key, 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "rows": len(normalized),
        "role_counts": dict(sorted(counts.items())),
        "claim_allowed": False,
    }
