"""Identity-bound dependency verification and restart lifecycle for ICML lanes."""

from __future__ import annotations

import importlib
import importlib.metadata
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

MODES = {
    "USE_PREINSTALLED_VALIDATED",
    "KAGGLE_INTERNET_ON_INSTALL",
    "PRIVATE_WHEELHOUSE_OFFLINE",
}


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True).encode() + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise
MARKER_FIELDS = (
    "lane",
    "input_zip_sha256",
    "source_tree_sha256",
    "dependency_profile_id",
    "dependency_lock_sha256",
    "python_version",
    "platform",
    "claim_allowed",
)


def load_dependency_profile(lane: str, path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or lane not in profiles:
        raise ValueError(f"no frozen dependency profile for lane {lane}")
    profile = dict(profiles[lane])
    lock = profile.get("lock")
    if not isinstance(lock, list) or not lock:
        raise ValueError("dependency profile requires a non-empty exact lock")
    for row in lock:
        if not isinstance(row, dict) or not all(row.get(key) for key in ("distribution", "import_name", "version")):
            raise ValueError("dependency lock rows require distribution/import_name/version")
    profile["dependency_lock_sha256"] = _stable_hash(lock)
    profile["profile_file_sha256"] = _file_sha256(path)
    profile["claim_allowed"] = False
    return profile


def dependency_marker_identity(
    *,
    lane: str,
    input_zip_sha256: str,
    source_tree_sha256: str,
    profile: Mapping[str, Any],
    python_version: str | None = None,
    platform_id: str | None = None,
) -> dict[str, Any]:
    identity = {
        "lane": lane,
        "input_zip_sha256": input_zip_sha256,
        "source_tree_sha256": source_tree_sha256,
        "dependency_profile_id": profile["dependency_profile_id"],
        "dependency_lock_sha256": profile["dependency_lock_sha256"],
        "python_version": python_version or platform.python_version(),
        "platform": platform_id or platform.platform(),
        "claim_allowed": False,
    }
    for field in ("input_zip_sha256", "source_tree_sha256", "dependency_lock_sha256"):
        value = identity[field]
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"{field} must be an exact SHA-256")
    return identity


def validate_restart_marker(marker: Mapping[str, Any], expected: Mapping[str, Any]) -> dict[str, Any]:
    mismatches = [field for field in MARKER_FIELDS if marker.get(field) != expected.get(field)]
    if marker.get("schema_version") != "certgen.icml2027.dependency_restart_marker.v1":
        mismatches.append("schema_version")
    return {
        "passed": not mismatches,
        "mismatches": sorted(set(mismatches)),
        "claim_allowed": False,
    }


def evaluate_dependency_state(
    profile: Mapping[str, Any],
    installed_versions: Mapping[str, str],
) -> dict[str, Any]:
    missing: list[str] = []
    incompatible: list[dict[str, str]] = []
    for row in profile["lock"]:
        distribution = str(row["distribution"])
        expected = str(row["version"])
        actual = installed_versions.get(distribution)
        if actual is None:
            missing.append(distribution)
        elif actual != expected:
            incompatible.append({"distribution": distribution, "expected": expected, "actual": actual})
    return {
        "passed": not missing and not incompatible,
        "missing": sorted(missing),
        "incompatible": incompatible,
        "claim_allowed": False,
    }


def plan_dependency_action(
    state: Mapping[str, Any],
    *,
    mode: str,
    wheelhouse_distributions: set[str] | None = None,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"unsupported dependency mode: {mode}")
    required = set(state.get("missing", [])) | {
        str(row["distribution"]) for row in state.get("incompatible", [])
    }
    if not required:
        return {"action": "VERIFY_PREINSTALLED", "restart_required": False, "claim_allowed": False}
    if mode == "USE_PREINSTALLED_VALIDATED":
        raise RuntimeError("preinstalled environment is missing or incompatible with the frozen lock")
    if mode == "PRIVATE_WHEELHOUSE_OFFLINE":
        available = wheelhouse_distributions or set()
        absent = sorted(required - available)
        if absent:
            raise RuntimeError(f"offline wheelhouse does not cover frozen lock entries: {absent}")
    return {
        "action": "INSTALL_EXACT_LOCK",
        "restart_required": True,
        "required_distributions": sorted(required),
        "claim_allowed": False,
    }


def _installed_versions(profile: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in profile["lock"]:
        distribution = str(row["distribution"])
        try:
            result[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            continue
    return result


def _run_checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"dependency command failed ({result.returncode}): {' '.join(command)}; "
            f"stdout={result.stdout[-1000:]}; stderr={result.stderr[-1000:]}"
        )
    return result


def _pip_install(profile: Mapping[str, Any], mode: str, wheelhouse: str | Path | None) -> None:
    requirements = [f"{row['distribution']}=={row['version']}" for row in profile["lock"]]
    command = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
    if mode == "PRIVATE_WHEELHOUSE_OFFLINE":
        if wheelhouse is None:
            raise RuntimeError("offline dependency mode requires an authenticated wheelhouse")
        command.extend(["--no-index", "--find-links", str(Path(wheelhouse))])
    command.extend(requirements)
    _run_checked(command)


def _verify_runtime(profile: Mapping[str, Any]) -> dict[str, Any]:
    pip_check = _run_checked([sys.executable, "-m", "pip", "check"])
    imported: list[str] = []
    for name in profile.get("import_smoke", []):
        importlib.import_module(str(name))
        imported.append(str(name))
    return {
        "pip_check": "PASS",
        "pip_check_stdout": pip_check.stdout.strip(),
        "imports": imported,
        "claim_allowed": False,
    }


def ensure_dependency_lifecycle(
    *,
    lane: str,
    input_zip_sha256: str,
    source_tree_sha256: str,
    profile_path: str | Path,
    marker_path: str | Path,
    report_path: str | Path,
    mode: str,
    wheelhouse: str | Path | None = None,
    installed_versions_override: Mapping[str, str] | None = None,
    install_hook: Callable[[Mapping[str, Any], str, str | Path | None], None] | None = None,
    verify_hook: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    python_version: str | None = None,
    platform_id: str | None = None,
) -> dict[str, Any]:
    """Verify/install an exact lock and bind any restart to scientific input identity."""

    profile = load_dependency_profile(lane, profile_path)
    expected = dependency_marker_identity(
        lane=lane,
        input_zip_sha256=input_zip_sha256,
        source_tree_sha256=source_tree_sha256,
        profile=profile,
        python_version=python_version,
        platform_id=platform_id,
    )
    marker_file = Path(marker_path)
    previous: dict[str, Any] | None = None
    if marker_file.is_file():
        previous = json.loads(marker_file.read_text(encoding="utf-8"))
        validation = validate_restart_marker(previous, expected)
        if not validation["passed"]:
            raise RuntimeError(f"stale or wrong dependency restart marker rejected: {validation['mismatches']}")
    installed = dict(installed_versions_override or _installed_versions(profile))
    state = evaluate_dependency_state(profile, installed)
    wheelhouse_names = {str(row["distribution"]) for row in profile["lock"]} if wheelhouse else None
    plan = plan_dependency_action(state, mode=mode, wheelhouse_distributions=wheelhouse_names)
    restart_required = False
    if plan["action"] == "INSTALL_EXACT_LOCK":
        installer = install_hook or _pip_install
        installer(profile, mode, wheelhouse)
        restart_required = True
        if installed_versions_override is not None:
            installed = {str(row["distribution"]): str(row["version"]) for row in profile["lock"]}
        else:
            installed = _installed_versions(profile)
    state_after = evaluate_dependency_state(profile, installed)
    if not state_after["passed"]:
        raise RuntimeError("dependency installation did not produce the exact frozen lock")
    verification = dict((verify_hook or _verify_runtime)(profile))
    marker = {
        "schema_version": "certgen.icml2027.dependency_restart_marker.v1",
        **expected,
        "mode": mode,
        "status": "VERIFIED_RESTART_REQUIRED" if restart_required else "VERIFIED_COMPLETE",
        "installed_versions": installed,
        "verification_hash": _stable_hash(verification),
    }
    _write_json(marker_file, marker)
    report = {
        "schema_version": "certgen.icml2027.dependency_verification.v1",
        "passed": True,
        "identity": expected,
        "profile_file_sha256": profile["profile_file_sha256"],
        "state_before": state,
        "state_after": state_after,
        "plan": plan,
        "verification": verification,
        "restart_required": restart_required,
        "second_pass_identity_verified": previous is not None,
        "claim_allowed": False,
    }
    _write_json(report_path, report)
    return report


def dependency_mode_from_environment() -> str:
    mode = os.environ.get("CERTGEN_DEPENDENCY_MODE", "USE_PREINSTALLED_VALIDATED")
    if mode not in MODES:
        raise ValueError(f"invalid CERTGEN_DEPENDENCY_MODE: {mode}")
    return mode
