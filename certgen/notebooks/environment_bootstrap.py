"""Idempotent, fail-closed Kaggle environment bootstrap planning and execution.

Normal local tests only exercise inspection and planning.  Package installation is
performed only when ``apply=True`` is explicitly supplied by a real notebook.
"""

from __future__ import annotations

import importlib.metadata
import importlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from packaging.requirements import Requirement

from certgen.cvpr.contracts import atomic_write_json


EVIDENCE_LABELS = {
    "evidence_class": "non_evidence_preflight",
    "not_empirical_evidence": True,
    "claim_allowed": False,
}

COMPATIBILITY_PROFILES: dict[str, tuple[str, ...]] = {
    "kaggle_t4x2_diagnostic": (
        "torch==2.7.1",
        "numpy>=2.0,<2.1",
        "PyYAML==6.0.2",
        "packaging==25.0",
    ),
    "kaggle_t4x2_generation": (
        "torch==2.7.1",
        "torchvision==0.22.1",
        "diffusers==0.34.0",
        "transformers==4.53.2",
        "accelerate==1.8.1",
        "safetensors==0.5.3",
        "Pillow==11.2.1",
        "numpy>=2.0,<2.1",
        "scipy>=1.13,<1.16",
        "scikit-learn>=1.5,<1.8",
        "huggingface-hub>=0.33,<0.35",
    ),
    "kaggle_t4x2_features": (
        "torch==2.7.1",
        "torchvision==0.22.1",
        "transformers==4.53.2",
        "safetensors==0.5.3",
        "Pillow==11.2.1",
        "numpy>=2.0,<2.1",
        "scipy>=1.13,<1.16",
        "scikit-learn>=1.5,<1.8",
        "huggingface-hub>=0.33,<0.35",
    ),
    "kaggle_t4x2_preflight": (
        "torch==2.7.1",
        "torchvision==0.22.1",
        "diffusers==0.34.0",
        "transformers==4.53.2",
        "accelerate==1.8.1",
        "safetensors==0.5.3",
        "Pillow==11.2.1",
        "numpy>=2.0,<2.1",
        "scipy>=1.13,<1.16",
        "scikit-learn>=1.5,<1.8",
        "huggingface-hub>=0.33,<0.35",
    ),
}

PROFILE_LOCKS = {
    "kaggle_t4x2_diagnostic": "kaggle-diagnostic.lock",
    "kaggle_t4x2_preflight": "kaggle-preflight.lock",
    "kaggle_t4x2_generation": "kaggle-generation.lock",
    "kaggle_t4x2_features": "kaggle-features.lock",
}

IMPORT_NAMES = {
    "Pillow": "PIL",
    "PyYAML": "yaml",
    "scikit-learn": "sklearn",
    "huggingface-hub": "huggingface_hub",
}

INSTALL_MODES = {
    "KAGGLE_INTERNET_ON_INSTALL",
    "PRIVATE_WHEELHOUSE_OFFLINE",
    "USE_PREINSTALLED_VALIDATED",
}


@dataclass(frozen=True)
class PackageObservation:
    requirement: str
    distribution: str
    installed_version: str | None
    compatible: bool
    reason: str


def _version_getter(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def inspect_profile(
    profile: str,
    *,
    version_getter: Callable[[str], str | None] = _version_getter,
) -> list[PackageObservation]:
    if profile not in COMPATIBILITY_PROFILES:
        raise ValueError(f"unknown compatibility profile: {profile}")
    rows: list[PackageObservation] = []
    for raw in COMPATIBILITY_PROFILES[profile]:
        requirement = Requirement(raw)
        installed = version_getter(requirement.name)
        compatible = installed is not None and installed in requirement.specifier
        reason = "compatible" if compatible else ("missing" if installed is None else "incompatible")
        rows.append(PackageObservation(raw, requirement.name, installed, compatible, reason))
    return rows


def installation_plan(observations: Sequence[PackageObservation]) -> list[str]:
    return [row.requirement for row in observations if not row.compatible]


def _pip_version() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _lock_snapshot() -> list[str]:
    return sorted(f"{dist.metadata['Name']}=={dist.version}" for dist in importlib.metadata.distributions())


def _write_lock(path: Path, rows: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text("\n".join(rows) + "\n", encoding="utf-8")
    temporary.replace(path)


def _lock_requirements(path: Path, seen: set[Path] | None = None) -> tuple[str, ...]:
    visited = seen or set()
    resolved = path.resolve()
    if resolved in visited:
        return ()
    visited.add(resolved)
    rows: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "-c")):
            continue
        if line.startswith("-r "):
            rows.extend(_lock_requirements(path.parent / line[3:].strip(), visited))
        else:
            Requirement(line)
            rows.append(line)
    return tuple(rows)


def import_smoke_test(
    profile: str,
    *,
    importer: Callable[[str], Any] = importlib.import_module,
) -> dict[str, object]:
    modules: list[str] = []
    for raw in COMPATIBILITY_PROFILES[profile]:
        distribution = Requirement(raw).name
        module = IMPORT_NAMES.get(distribution, distribution.replace("-", "_"))
        if module not in modules:
            modules.append(module)
    modules.extend(
        [
            "certgen",
            "certgen.notebooks.kaggle_io",
            "certgen.notebooks.environment_bootstrap",
            "certgen.notebooks.model_assets",
        ]
    )
    rows: list[dict[str, object]] = []
    for module in modules:
        try:
            importer(module)
        except Exception as exc:
            rows.append({"module": module, "passed": False, "error": f"{type(exc).__name__}: {exc}"})
        else:
            rows.append({"module": module, "passed": True, "error": None})
    return {
        "schema_version": "certgen.import_smoke_test.v1",
        "profile": profile,
        "passed": all(row["passed"] for row in rows),
        "imports": rows,
        **EVIDENCE_LABELS,
    }


def bootstrap_environment(
    profile: str,
    *,
    output_dir: str | Path,
    network_allowed: bool,
    apply: bool = False,
    revalidate_after_restart: bool = False,
    version_getter: Callable[[str], str | None] = _version_getter,
    installer: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    pip_checker: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    importer: Callable[[str], Any] = importlib.import_module,
    install_mode: str | None = None,
    wheelhouse: str | Path | None = None,
    search_roots: Iterable[str | Path] | None = None,
    lock_path: str | Path | None = None,
    constraints_path: str | Path | None = None,
) -> dict[str, object]:
    """Inspect, optionally repair, and record one compatibility profile.

    ``apply=False`` is a side-effect-free planning/inspection mode.  A missing
    dependency with network disabled fails before pip is invoked.
    """

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    before = inspect_profile(profile, version_getter=version_getter)
    plan = installation_plan(before)
    selected_mode = install_mode or (
        "KAGGLE_INTERNET_ON_INSTALL" if network_allowed else "USE_PREINSTALLED_VALIDATED"
    )
    if selected_mode not in INSTALL_MODES:
        raise ValueError(f"unknown dependency install mode: {selected_mode}")
    install_log = out / "pip_install.log"
    restart_marker = out / "kernel_restart_required.json"
    install_returncode: int | None = None
    install_output = "installation not requested"
    requirements_root = Path(__file__).resolve().parents[2] / "requirements"
    selected_lock = Path(lock_path) if lock_path is not None else requirements_root / PROFILE_LOCKS[profile]
    selected_constraints = Path(constraints_path) if constraints_path is not None else requirements_root / "kaggle-constraints.txt"
    resolved_wheelhouse: Path | None = None

    if apply and plan:
        if selected_mode == "USE_PREINSTALLED_VALIDATED":
            if not network_allowed and install_mode is None:
                raise RuntimeError("offline bootstrap cannot repair missing or incompatible packages")
            raise RuntimeError("USE_PREINSTALLED_VALIDATED cannot repair missing or incompatible packages")
        if selected_mode == "KAGGLE_INTERNET_ON_INSTALL" and not network_allowed:
            raise RuntimeError("offline bootstrap cannot repair missing or incompatible packages")
        if selected_mode == "PRIVATE_WHEELHOUSE_OFFLINE" and network_allowed:
            raise RuntimeError("PRIVATE_WHEELHOUSE_OFFLINE requires dependency network disabled")
        if not selected_lock.is_file() or not selected_constraints.is_file():
            raise RuntimeError("stage lock or compatibility constraints are missing")
        install_prefix = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
        if selected_mode == "PRIVATE_WHEELHOUSE_OFFLINE":
            from certgen.discovery import discover_wheelhouse

            wheelhouse_roots = tuple(search_roots or (() if wheelhouse is None else (wheelhouse,)))
            if not wheelhouse_roots:
                raise RuntimeError("private wheelhouse search roots are missing")
            resolution = discover_wheelhouse(
                wheelhouse_roots,
                profile=profile,
                required_requirements=_lock_requirements(selected_lock),
            )
            selected = resolution.get("selected")
            if not isinstance(selected, dict) or not selected.get("root"):
                raise RuntimeError(f"private wheelhouse discovery failed: {resolution['status']}")
            resolved_wheelhouse = Path(str(selected["root"]))
            install_prefix.extend(
                [
                    "--no-index",
                    "--find-links",
                    str(resolved_wheelhouse),
                    "-c",
                    str(selected_constraints),
                    "-r",
                    str(selected_lock),
                ]
            )
        else:
            install_prefix.extend(["-c", str(selected_constraints), *plan])
        result = installer(
            install_prefix,
            check=False,
            capture_output=True,
            text=True,
        )
        install_returncode = result.returncode
        install_output = (result.stdout or "") + (result.stderr or "")
        install_log.write_text(install_output, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"environment installation failed; see {install_log}")
        atomic_write_json(
            {
                "restart_required": True,
                "instruction": "Stop this cell, restart the Kaggle kernel, and rerun the environment bootstrap cell.",
                **EVIDENCE_LABELS,
            },
            restart_marker,
        )

    after = inspect_profile(profile, version_getter=version_getter)
    compatible = all(row.compatible for row in after)
    restart_required = bool(apply and plan and not revalidate_after_restart)
    status = "ENVIRONMENT_COMPATIBLE" if compatible and not restart_required else (
        "KERNEL_RESTART_REQUIRED" if restart_required else "ENVIRONMENT_INCOMPATIBLE"
    )
    lock_path = out / "requirements-lock.txt"
    freeze = _lock_snapshot()
    _write_lock(lock_path, freeze)
    _write_lock(out / "dependency_freeze.txt", freeze)
    pip_check = pip_checker(
        [sys.executable, "-m", "pip", "check"],
        check=False,
        capture_output=True,
        text=True,
    )
    (out / "pip_check.txt").write_text(
        (pip_check.stdout or "") + (pip_check.stderr or ""), encoding="utf-8"
    )
    smoke: dict[str, object]
    if apply and compatible and not restart_required:
        smoke = import_smoke_test(profile, importer=importer)
    else:
        smoke = {
            "schema_version": "certgen.import_smoke_test.v1",
            "profile": profile,
            "passed": None,
            "status": "NOT_RUN_UNTIL_COMPATIBLE_POST_RESTART_ENVIRONMENT",
            "imports": [],
            **EVIDENCE_LABELS,
        }
    atomic_write_json(smoke, out / "import_smoke_test.json")
    payload: dict[str, object] = {
        "schema_version": "certgen.environment_report.v1",
        "profile": profile,
        "status": status,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "pip_version": _pip_version(),
        "network_required": bool(plan),
        "network_allowed": network_allowed,
        "install_mode": selected_mode,
        "stage_lock": str(selected_lock),
        "constraints": str(selected_constraints),
        "resolved_wheelhouse": str(resolved_wheelhouse) if resolved_wheelhouse else None,
        "apply_requested": apply,
        "restart_required": restart_required,
        "restart_instruction": (
            "Restart the Kaggle kernel and rerun this cell with revalidate_after_restart=true."
            if restart_required
            else None
        ),
        "installation_plan": plan,
        "install_returncode": install_returncode,
        "install_log": str(install_log),
        "install_output_recorded": install_output != "installation not requested",
        "requirements_lock": str(lock_path),
        "dependency_freeze": str(out / "dependency_freeze.txt"),
        "pip_check": {"returncode": pip_check.returncode, "path": str(out / "pip_check.txt")},
        "import_smoke_test": {"passed": smoke.get("passed"), "path": str(out / "import_smoke_test.json")},
        "packages_before": [asdict(row) for row in before],
        "packages_after": [asdict(row) for row in after],
        **EVIDENCE_LABELS,
    }
    atomic_write_json(payload, out / "environment_report.json")
    atomic_write_json(payload, out / "dependency_report.json")
    if apply and not compatible and not restart_required:
        raise RuntimeError("environment failed closed after package installation/revalidation")
    if apply and compatible and not restart_required and pip_check.returncode != 0:
        raise RuntimeError("python -m pip check failed; see pip_check.txt")
    if apply and compatible and not restart_required and smoke.get("passed") is not True:
        raise RuntimeError("post-install import smoke test failed; see import_smoke_test.json")
    return payload


def load_environment_report(path: str | Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("claim_allowed") is not False:
        raise ValueError("invalid environment report")
    return payload
