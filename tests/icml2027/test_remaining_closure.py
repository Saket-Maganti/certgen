from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import types
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image

from certgen.features.extractors.dinov2 import DinoV2Extractor
from certgen.generation.generate_cifar10_diffusers import run_generation_samples
from certgen.icml2027.common import file_sha256, stable_hash
from certgen.icml2027.execution_contract import (
    CONFIG_SHA256,
    MODEL_CHECKPOINTS,
    REFERENCE_PLAN_SHA256,
    STUDY_HASH,
    STUDY_ID,
    build_dinov2_preflight_worker_spec,
    build_execution_contract,
    build_feature_worker_spec,
    build_generation_worker_spec,
    build_generator_seed_manifest,
    validate_worker_spec,
)
from certgen.icml2027.feature_provenance import (
    build_actual_extractor_provenance,
    validate_actual_extractor_provenance,
)
from certgen.icml2027.notebooks import _bootstrap_code
from certgen.icml2027.kaggle import build_input, compute_prerequisite_identity
from certgen.icml2027.payload import (
    build_multipart_payload,
    import_multipart_payload,
    validate_multipart_payload,
)


ROOT = Path(__file__).resolve().parents[2]


def _source(role: str, *, shards: int = 2) -> dict[str, object]:
    ids = [f"{role}-{index}" for index in range(4)]
    shard_ids = [ids[shard::shards] for shard in range(shards)]
    return {
        "source_role": role,
        "runtime_manifest_path": f"inputs/manifests/{role}.jsonl",
        "runtime_provenance_ledger": f"inputs/provenance/{role}.jsonl",
        "manifest_sha256": stable_hash({"role": role, "kind": "manifest"}),
        "payload_sha256": stable_hash({"role": role, "kind": "payload"}),
        "sample_ids_sha256": stable_hash(ids),
        "row_order_sha256": stable_hash(ids),
        "shard_sample_ids_sha256": [stable_hash(values) for values in shard_ids],
        "expected_row_count": len(ids),
        "claim_allowed": False,
    }


def _extractor(extractor_id: str) -> dict[str, object]:
    values = {
        "inception": (
            "inception_v3_pool3",
            "torchvision_inception_v3_IMAGENET1K_V1",
            "torchvision_0.22.1__Inception_V3_Weights.IMAGENET1K_V1",
            "torchvision.models.Inception3",
            "torchvision.transforms.Compose",
            "final_global_average_pool_before_fc_2048d",
            2048,
            "none",
            "inception-v3.pth",
        ),
        "clip": (
            "clip_vit",
            "openai/clip-vit-large-patch14",
            "32bd64288804d66eefd0ccbe215aa642df71cc41",
            "transformers.CLIPModel",
            "transformers.CLIPProcessor",
            "projected_image_embedding_from_CLIPModel.get_image_features",
            768,
            "l2",
            None,
        ),
        "dinov2": (
            "dinov2",
            "facebook/dinov2-base",
            "f9e44c814b77203eaa57a6bdbbd535f21ede1415",
            "transformers.Dinov2Model",
            "transformers.AutoImageProcessor",
            "last_hidden_state[:,0,:]",
            768,
            "none",
            None,
        ),
    }
    runtime, model, revision, model_class, processor, layer, dimension, normalization, weight = values[
        extractor_id
    ]
    return {
        "extractor_id": extractor_id,
        "runtime_extractor": runtime,
        "model_identifier": model,
        "revision": revision,
        "model_class": model_class,
        "processor_identity": processor,
        "feature_layer": layer,
        "dimension": dimension,
        "dtype": "float32",
        "normalization": normalization,
        "preprocessing_sha256": stable_hash({"extractor": extractor_id}),
        "runtime_preprocessing_lock": f"inputs/preprocessing/{extractor_id}.json",
        "asset_id": f"{extractor_id}__asset",
        "asset_manifest_sha256": stable_hash({"extractor": extractor_id, "kind": "manifest"}),
        "asset_inventory_sha256": stable_hash({"extractor": extractor_id, "kind": "inventory"}),
        "aggregate_manifest_sha256": stable_hash({"kind": "aggregate"}),
        "loader_type": "torchvision_local_state_dict"
        if extractor_id == "inception"
        else "from_pretrained_local_snapshot",
        "local_files_only": True,
        "local_weight_file": weight,
        "claim_allowed": False,
    }


def _feature_spec(lane: str) -> dict[str, Any]:
    manifest = build_generator_seed_manifest(count_per_model=4)
    contract = build_execution_contract(manifest, root=ROOT)
    roles = (
        ["reference", *MODEL_CHECKPOINTS]
        if lane == "cifar_10k_features"
        else ["reference", "candidate"]
    )
    extractor_ids = ["inception", "clip"] if lane != "dinov2_features" else ["dinov2"]
    return build_feature_worker_spec(
        lane=lane,
        input_package_sha256="a" * 64,
        study_id=STUDY_ID if lane == "cifar_10k_features" else f"{lane}_fixture",
        study_hash=STUDY_HASH if lane == "cifar_10k_features" else "b" * 64,
        configuration_sha256=CONFIG_SHA256 if lane == "cifar_10k_features" else "c" * 64,
        seed_plan_sha256=contract["seed_plan_sha256"],
        sample_identity_policy_sha256=contract["sample_identity_policy_sha256"],
        source_manifests={role: _source(role) for role in roles},
        extractor_specs={extractor_id: _extractor(extractor_id) for extractor_id in extractor_ids},
        shards_per_source=2,
        reference_plan_sha256=REFERENCE_PLAN_SHA256,
        expected_prefix_hashes=contract["expected_prefix_hashes"],
        model_revisions=contract["models"],
    )


@pytest.mark.parametrize(
    "lane", ["cifar_10k_features", "dinov2_features", "released_sample_features"]
)
def test_canonical_feature_worker_spec_builders(lane: str) -> None:
    spec = _feature_spec(lane)
    contract = None
    if lane == "cifar_10k_features":
        contract = build_execution_contract(build_generator_seed_manifest(count_per_model=4), root=ROOT)
    validation = validate_worker_spec(spec, expected_lane=lane, contract=contract)
    assert validation["passed"], validation["errors"]
    assert len(spec["jobs"]) == len(spec["extractor_specs"]) * len(spec["source_manifests"]) * 2
    assert spec["claim_allowed"] is False
    if lane == "dinov2_features":
        assert spec["robustness_feature_space"] is True
        assert spec["confirmatory_family"] is False


def test_canonical_dinov2_preflight_worker_spec() -> None:
    spec = build_dinov2_preflight_worker_spec(
        input_package_sha256="a" * 64,
        asset_manifest_sha256="b" * 64,
        asset_inventory_sha256="c" * 64,
        root=ROOT,
    )
    assert validate_worker_spec(
        spec, expected_lane="dinov2_preflight", contract=None
    )["passed"]
    mutated = copy.deepcopy(spec)
    mutated["asset_requirement"]["revision"] = "wrong"
    assert not validate_worker_spec(
        mutated, expected_lane="dinov2_preflight", contract=None
    )["passed"]


def test_feature_worker_spec_mutations_fail_closed() -> None:
    spec = _feature_spec("cifar_10k_features")
    contract = build_execution_contract(build_generator_seed_manifest(count_per_model=4), root=ROOT)
    mutations = []
    for field in ("extractor_revision", "preprocessing_sha256", "source_manifest_sha256"):
        mutated = copy.deepcopy(spec)
        mutated["jobs"][0][field] = "0" * 64
        mutations.append(mutated)
    missing = copy.deepcopy(spec)
    missing["jobs"].pop()
    mutations.append(missing)
    extra = copy.deepcopy(spec)
    extra["extractor_specs"]["dinov2"] = _extractor("dinov2")
    mutations.append(extra)
    wrong_order = copy.deepcopy(spec)
    wrong_order["jobs"][0]["source_sample_order_sha256"] = "0" * 64
    mutations.append(wrong_order)
    for mutated in mutations:
        assert not validate_worker_spec(
            mutated, expected_lane="cifar_10k_features", contract=contract
        )["passed"]
    dino = _feature_spec("dinov2_features")
    dino["confirmatory_family"] = True
    assert not validate_worker_spec(dino, expected_lane="dinov2_features", contract=None)[
        "passed"
    ]


def test_actual_extractor_provenance_mutations_fail() -> None:
    job = next(
        row
        for row in _feature_spec("dinov2_features")["jobs"]
        if row["source_role"] == "reference" and row["shard_id"] == 0
    )
    expected = job["runtime_provenance_expectation"]
    ids = ["reference-0", "reference-2"]
    sidecar = {
        "extractor": "dinov2",
        "model_id": "facebook/dinov2-base",
        "model_revision": "f9e44c814b77203eaa57a6bdbbd535f21ede1415",
        "model_class": "transformers.Dinov2Model",
        "processor_identity": "transformers.AutoImageProcessor",
        "preprocessing": {"extractor": "dinov2"},
        "preprocessing_sha256": stable_hash({"extractor": "dinov2"}),
        "feature_layer": "last_hidden_state[:,0,:]",
        "feature_dim": 768,
        "dtype": "float32",
        "feature_normalization": "none",
        "sample_ids": ids,
        "local_files_only": True,
        "dependency_versions": {"transformers": "fixture"},
        "device": "cpu",
    }
    asset = {
        "asset_id": "dinov2__asset",
        "revision": sidecar["model_revision"],
        "asset_manifest_sha256": expected["asset_manifest_sha256"],
        "inventory_sha256": expected["asset_inventory_sha256"],
        "aggregate_manifest_sha256": expected["aggregate_manifest_sha256"],
        "runtime_snapshot_root": "/runtime-only/fixture",
    }
    actual = build_actual_extractor_provenance(
        sidecar,
        extractor_id="dinov2",
        source_role="reference",
        source_manifest_sha256=expected["source_manifest_sha256"],
        source_payload_sha256=expected["source_payload_sha256"],
        sample_ids=ids,
        asset_identity=asset,
        output_schema_version="certgen.icml2027.feature_payload.v1",
    )
    assert validate_actual_extractor_provenance(actual, expected)["passed"]
    for field, value in (
        ("model_revision", "wrong"),
        ("preprocessing_sha256", "0" * 64),
        ("dimension", 7),
        ("processor_identity", "wrong"),
        ("row_order_sha256", "0" * 64),
        ("source_manifest_sha256", "0" * 64),
    ):
        mutated = copy.deepcopy(actual)
        mutated[field] = value
        mutated["actual_provenance_sha256"] = stable_hash(
            {key: item for key, item in mutated.items() if key != "actual_provenance_sha256"}
        )
        assert not validate_actual_extractor_provenance(mutated, expected)["passed"]


@pytest.mark.parametrize(
    "lane", ["cifar_10k_features", "dinov2_features", "released_sample_features"]
)
def test_actual_provenance_multipart_feature_rehearsal(
    lane: str, tmp_path: Path
) -> None:
    spec = _feature_spec(lane)
    parts: list[dict[str, bytes]] = []
    records: list[dict[str, object]] = []
    for job in spec["jobs"]:
        extractor_id = str(job["extractor_id"])
        source_role = str(job["source_role"])
        shard_id = int(job["shard_id"])
        expected = job["runtime_provenance_expectation"]
        sample_ids = [f"{source_role}-{shard_id}", f"{source_role}-{shard_id + 2}"]
        features: np.ndarray = np.full(
            (len(sample_ids), int(job["expected_dimension"])),
            fill_value=shard_id + 1,
            dtype=np.float32,
        )
        buffer = io.BytesIO()
        np.savez_compressed(buffer, features=features, sample_ids=np.asarray(sample_ids))
        observed = {
            "extractor": expected["runtime_extractor"],
            "model_id": expected["model_identifier"],
            "model_revision": expected["model_revision"],
            "model_class": expected["model_class"],
            "processor_identity": expected["processor_identity"],
            "preprocessing": {"extractor": extractor_id},
            "preprocessing_sha256": expected["preprocessing_sha256"],
            "feature_layer": expected["feature_layer"],
            "feature_dim": expected["dimension"],
            "dtype": expected["dtype"],
            "feature_normalization": expected["normalization"],
            "sample_ids": sample_ids,
            "local_files_only": True,
            "dependency_versions": {"fixture": "1"},
            "device": "cpu",
        }
        asset = {
            "asset_id": expected["asset_id"],
            "revision": expected["asset_revision"],
            "asset_manifest_sha256": expected["asset_manifest_sha256"],
            "inventory_sha256": expected["asset_inventory_sha256"],
            "aggregate_manifest_sha256": expected["aggregate_manifest_sha256"],
            "runtime_snapshot_root": "fixture-only-not-scientific-identity",
        }
        actual = build_actual_extractor_provenance(
            observed,
            extractor_id=extractor_id,
            source_role=source_role,
            source_manifest_sha256=str(job["source_manifest_sha256"]),
            source_payload_sha256=str(job["source_payload_sha256"]),
            sample_ids=sample_ids,
            asset_identity=asset,
            output_schema_version=str(spec["output_schema_version"]),
        )
        assert validate_actual_extractor_provenance(actual, expected)["passed"]
        stem = f"{extractor_id}/{source_role}/shard-{shard_id:03d}"
        feature_path = f"features/{stem}.npz"
        sidecar_path = f"sidecars/{stem}.json"
        parts.append(
            {
                feature_path: buffer.getvalue(),
                sidecar_path: (json.dumps(actual, sort_keys=True) + "\n").encode(),
            }
        )
        records.append(
            {
                "extractor_id": extractor_id,
                "extractor_revision": actual["model_revision"],
                "preprocessing_sha256": actual["preprocessing_sha256"],
                "source_role": source_role,
                "source_manifest_sha256": actual["source_manifest_sha256"],
                "source_payload_sha256": actual["source_payload_sha256"],
                "feature_path": feature_path,
                "sidecar_path": sidecar_path,
                "dimension": actual["dimension"],
                "dtype": actual["dtype"],
                "row_count": actual["row_count"],
                "source_sample_ids_sha256": actual["source_sample_ids_sha256"],
                "actual_provenance_sha256": actual["actual_provenance_sha256"],
                "shard_id": shard_id,
                "claim_allowed": False,
            }
        )
    portable_spec = json.loads(json.dumps(spec))
    identity = {
        "input_package_sha256": spec["input_package_sha256"],
        "study_id": spec["study_id"],
        "study_hash": spec["study_hash"],
        "configuration_sha256": spec["configuration_sha256"],
        "worker_spec_sha256": stable_hash(portable_spec),
        "source_tree_sha256": "1" * 64,
        "dependency_lock_sha256": "2" * 64,
        "model_revisions": spec["model_revisions"],
        "extractor_revisions": spec["extractor_revisions"],
        "preprocessing_hashes": spec["preprocessing_hashes"],
        "reference_plan_sha256": spec["reference_plan_sha256"],
        "seed_manifest_sha256": "3" * 64,
        "robustness_feature_space": lane == "dinov2_features",
        "confirmatory_family": False if lane == "dinov2_features" else True,
        "claim_allowed": False,
    }
    built = build_multipart_payload(
        lane=lane,
        payload_type="features",
        parts=parts,
        records=records,
        identity=identity,
        out_dir=tmp_path,
        basename=lane,
    )
    worker_spec_path = tmp_path / f"{lane}.worker.json"
    worker_spec_path.write_text(json.dumps(portable_spec), encoding="utf-8")
    validation = validate_multipart_payload(
        built["index_path"],
        expected_type="features",
        worker_spec_path=worker_spec_path,
    )
    assert validation["passed"]
    receipt = import_multipart_payload(built["index_path"], tmp_path / "imported")
    assert receipt["validation"]["passed"]


def _package(path: Path, lane: str = "cifar_10k_generation") -> dict[str, object]:
    member = b"trusted source\n"
    worker = b'{"claim_allowed":false}\n'
    inventory = [
        {"path": "inputs/worker_spec.json", "sha256": hashlib.sha256(worker).hexdigest(), "bytes": len(worker)},
        {"path": "source/certgen/__init__.py", "sha256": hashlib.sha256(member).hexdigest(), "bytes": len(member)},
    ]
    manifest = {
        "schema_version": "certgen.icml2027.kaggle_input.v1",
        "lane": lane,
        "configuration_sha256": "1" * 64,
        "authenticated_prerequisite_set_sha256": "2" * 64,
        "source_tree_sha256": "3" * 64,
        "input_hashes": {"worker_spec": {"members": [inventory[0]]}},
        "inventory": inventory,
        "claim_allowed": False,
    }
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("inputs/worker_spec.json", worker)
        archive.writestr("source/certgen/__init__.py", member)
        archive.writestr("package_manifest.json", manifest_bytes)
    identity = {
        "schema_version": "certgen.icml2027.expected_input.v1",
        "expected_lane": lane,
        "expected_input_zip_sha256": file_sha256(path),
        "expected_package_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "expected_configuration_sha256": manifest["configuration_sha256"],
        "expected_source_tree_sha256": manifest["source_tree_sha256"],
        "expected_prerequisite_set_sha256": manifest["authenticated_prerequisite_set_sha256"],
        "expected_worker_spec_sha256": inventory[0]["sha256"],
        "claim_allowed": False,
    }
    identity["expected_identity_sha256"] = stable_hash(identity)
    return identity


def _execute_bootstrap(code: str, input_root: Path, work_root: Path) -> dict[str, Any]:
    patched = code.replace('Path("/kaggle/input")', f"Path({str(input_root)!r})")
    patched = patched.replace('Path("/kaggle/working")', f"Path({str(work_root)!r})")
    namespace: dict[str, object] = {}
    exec(compile(patched, "<icml-bootstrap-fixture>", "exec"), namespace)
    return namespace


def test_self_contained_bootstrap_renaming_duplicates_and_mutations(tmp_path: Path) -> None:
    input_root = tmp_path / "arbitrary-account" / "nested-dataset"
    input_root.mkdir(parents=True)
    package = input_root / "renamed-anything.zip"
    identity = _package(package)
    duplicate = input_root / "deeper" / "copy.zip"
    duplicate.parent.mkdir()
    duplicate.write_bytes(package.read_bytes())
    code = _bootstrap_code("cifar_10k_generation", identity)
    namespace = _execute_bootstrap(code, tmp_path / "arbitrary-account", tmp_path / "working")
    assert namespace["INPUT_ROOT"] == tmp_path / "working" / "certgen-authenticated-cifar_10k_generation"

    wrong_sha = copy.deepcopy(identity)
    wrong_sha["expected_input_zip_sha256"] = "0" * 64
    wrong_sha["expected_identity_sha256"] = stable_hash(
        {key: value for key, value in wrong_sha.items() if key != "expected_identity_sha256"}
    )
    with pytest.raises(RuntimeError, match="not found"):
        _execute_bootstrap(
            _bootstrap_code("cifar_10k_generation", wrong_sha),
            tmp_path / "arbitrary-account",
            tmp_path / "wrong-working",
        )
    wrong_lane = copy.deepcopy(identity)
    wrong_lane["expected_lane"] = "cifar_10k_features"
    wrong_lane["expected_identity_sha256"] = stable_hash(
        {key: value for key, value in wrong_lane.items() if key != "expected_identity_sha256"}
    )
    with pytest.raises(RuntimeError, match="another lane"):
        _execute_bootstrap(
            _bootstrap_code("cifar_10k_generation", wrong_lane),
            tmp_path / "arbitrary-account",
            tmp_path / "lane-working",
        )


def test_generic_bootstrap_uses_generated_launch_manifest_without_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CERTGEN_EXPECTED_ICML_INPUT_IDENTITY_JSON", raising=False)
    package = tmp_path / "mount" / "data" / "bundle.zip"
    package.parent.mkdir(parents=True)
    identity = _package(package)
    launch = {
        "schema_version": "certgen.icml2027.launch_manifest.v1",
        "expected_input_identity": identity,
        "launch_notebook": "exact.ipynb",
        "launch_notebook_sha256": "4" * 64,
        "claim_allowed": False,
    }
    launch["launch_manifest_sha256"] = stable_hash(launch)
    (package.parent / "certgen_icml2027_launch_manifest.v1.json").write_text(
        json.dumps(launch), encoding="utf-8"
    )
    namespace = _execute_bootstrap(
        _bootstrap_code("cifar_10k_generation"), tmp_path / "mount", tmp_path / "working"
    )
    assert namespace["EXPECTED_IDENTITY"]["expected_input_zip_sha256"] == file_sha256(package)
    stale = json.loads(json.dumps(launch))
    stale["expected_input_identity"]["expected_configuration_sha256"] = "0" * 64
    stale["expected_input_identity"]["expected_identity_sha256"] = stable_hash(
        {
            key: value
            for key, value in stale["expected_input_identity"].items()
            if key != "expected_identity_sha256"
        }
    )
    stale["launch_manifest_sha256"] = stable_hash(
        {key: value for key, value in stale.items() if key != "launch_manifest_sha256"}
    )
    (package.parent / "certgen_icml2027_launch_manifest.v1.json").write_text(
        json.dumps(stale), encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="stale or wrong"):
        _execute_bootstrap(
            _bootstrap_code("cifar_10k_generation"),
            tmp_path / "mount",
            tmp_path / "stale-working",
        )


def test_two_pass_builder_emits_self_authenticating_launch_pair(tmp_path: Path) -> None:
    prerequisites = tmp_path / "prerequisites"
    prerequisites.mkdir()
    legacy = prerequisites / "legacy-preflight.zip"
    legacy.write_bytes(b"authenticated-legacy-fixture")
    asset_manifest = prerequisites / "asset-manifest.json"
    asset_manifest.write_text('{"fixture": true}\n', encoding="utf-8")
    asset_root = prerequisites / "renamed-model-root"
    asset_root.mkdir()
    (asset_root / "weights.fixture").write_bytes(b"local-only-model-fixture")
    inputs: dict[str, str | Path] = {
        "legacy_preflight_output": legacy,
        "model_asset_manifest": asset_manifest,
        "model_asset_root": asset_root,
    }
    prerequisite_sha = compute_prerequisite_identity("cifar_10k_generation", inputs)
    manifest = json.loads(
        (
            ROOT
            / "registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json"
        ).read_text(encoding="utf-8")
    )
    contract = json.loads(
        (ROOT / "registry/icml2027/cifar_10k_v2_execution_contract_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assets = {
        model_id: {
            "asset_id": f"{model_id}__asset",
            "model_identifier": checkpoint["checkpoint_id"],
            "revision": checkpoint["checkpoint_revision"],
            "aggregate_manifest_sha256": "1" * 64,
            "asset_manifest_sha256": "2" * 64,
            "inventory_sha256": "3" * 64,
            "loader_type": "from_pretrained_local_snapshot",
            "local_files_only": True,
            "claim_allowed": False,
        }
        for model_id, checkpoint in MODEL_CHECKPOINTS.items()
    }
    worker = build_generation_worker_spec(
        manifest,
        contract,
        input_package_sha256=prerequisite_sha,
        asset_requirements=assets,
        shard_size=500,
    )
    worker_path = prerequisites / "worker.json"
    worker_path.write_text(json.dumps(worker), encoding="utf-8")
    inputs["worker_spec"] = worker_path
    result = build_input(
        "cifar_10k_generation",
        inputs,
        root=ROOT,
        out_root=tmp_path / "built",
    )
    assert result["input_zip_created"] is True
    assert result["manual_expected_identity_json_required"] is False
    assert Path(result["launch_notebook"]).is_file()
    assert Path(result["launch_manifest"]).is_file()
    mount = tmp_path / "arbitrary-mount"
    mount.mkdir()
    with zipfile.ZipFile(result["input_zip"]) as archive:
        archive.extractall(mount / "nested-package")
    copied_zip = mount / "renamed-input.zip"
    copied_zip.write_bytes(Path(result["input_zip"]).read_bytes())
    (mount / "certgen_icml2027_launch_manifest.v1.json").write_bytes(
        Path(result["launch_manifest"]).read_bytes()
    )
    namespace = _execute_bootstrap(
        _bootstrap_code("cifar_10k_generation"),
        mount,
        tmp_path / "working",
    )
    assert namespace["EXPECTED_IDENTITY"] == result["expected_input_identity"]


class _FakeImage:
    size = (32, 32)

    @staticmethod
    def getbands() -> tuple[str, str, str]:
        return ("R", "G", "B")

    @staticmethod
    def save(path: Path) -> None:
        Image.fromarray(np.zeros((32, 32, 3), dtype=np.uint8), mode="RGB").save(path)


def test_confirmatory_generation_loader_is_authenticated_local_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeGenerator:
        def __init__(self, device: str) -> None:
            self.device = device

        def manual_seed(self, seed: int) -> "FakeGenerator":
            return self

    class FakePipeline:
        @classmethod
        def from_pretrained(cls, root: str, **kwargs: object) -> "FakePipeline":
            calls.append((root, kwargs))
            return cls()

        def to(self, _device: str) -> "FakePipeline":
            return self

        def __call__(self, *, batch_size: int, generator: object) -> object:
            return types.SimpleNamespace(images=[_FakeImage() for _ in range(batch_size)])

    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(Generator=FakeGenerator))
    monkeypatch.setitem(sys.modules, "diffusers", types.SimpleNamespace(DDPMPipeline=FakePipeline))
    snapshot = tmp_path / "renamed-private-mount" / "snapshot"
    snapshot.mkdir(parents=True)
    model_id, checkpoint = next(iter(MODEL_CHECKPOINTS.items()))
    record = {
        "sample_id": "sample-0000",
        "sample_index": 0,
        "generator_seed": 7,
        "checkpoint_id": checkpoint["checkpoint_id"],
        "checkpoint_revision": checkpoint["checkpoint_revision"],
        "claim_allowed": False,
    }
    asset = {
        "asset_id": f"{model_id}__asset",
        "model_identifier": checkpoint["checkpoint_id"],
        "revision": checkpoint["checkpoint_revision"],
        "aggregate_manifest_sha256": "1" * 64,
        "asset_manifest_sha256": "2" * 64,
        "inventory_sha256": "3" * 64,
        "loader_type": "from_pretrained_local_snapshot",
        "local_files_only": True,
        "claim_allowed": False,
    }
    result = run_generation_samples(
        checkpoint_id=checkpoint["checkpoint_id"],
        samples=[record],
        out_dir=tmp_path / "images",
        manifest_out=tmp_path / "manifest.jsonl",
        device="cpu",
        batch_size=1,
        resume=False,
        authenticated_snapshot_root=snapshot,
        asset_identity=asset,
    )
    assert result["local_files_only"] is True
    assert calls == [(str(snapshot.resolve()), {"local_files_only": True})]


def test_dinov2_loader_uses_pinned_local_model_and_processor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str, dict[str, object]]] = []

    class FakeModel:
        config = types.SimpleNamespace(hidden_size=768)

        @classmethod
        def from_pretrained(cls, root: str, **kwargs: object) -> "FakeModel":
            calls.append(("model", root, kwargs))
            return cls()

        def eval(self) -> "FakeModel":
            return self

        def to(self, _device: str) -> "FakeModel":
            return self

    class FakeProcessor:
        @classmethod
        def from_pretrained(cls, root: str, **kwargs: object) -> "FakeProcessor":
            calls.append(("processor", root, kwargs))
            return cls()

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        types.SimpleNamespace(AutoModel=FakeModel, AutoImageProcessor=FakeProcessor),
    )
    snapshot = tmp_path / "arbitrary-dino-root"
    snapshot.mkdir()
    extractor = DinoV2Extractor()
    extractor.runtime_asset_context = {
        "model_identifier": "facebook/dinov2-base",
        "revision": "f9e44c814b77203eaa57a6bdbbd535f21ede1415",
        "runtime_snapshot_root": str(snapshot),
        "inventory_sha256": "1" * 64,
        "local_files_only": True,
    }
    extractor._load_backbone("cpu", None, {})
    assert calls == [
        ("model", str(snapshot), {"local_files_only": True}),
        ("processor", str(snapshot), {"local_files_only": True}),
    ]
    assert extractor.resolved_model_revision == "f9e44c814b77203eaa57a6bdbbd535f21ede1415"
    assert extractor.resolved_local_files_only is True


def test_planning_contract_and_boundary_registry_cannot_promote_unverified_methods() -> None:
    design = (
        ROOT / "docs/icml2027/theory/GENERATOR_DISTRIBUTION_RANDOMIZED_DESIGN.md"
    ).read_text(encoding="utf-8")
    assert "icml2027_generator_randomized_inference_v1" in design
    assert "PLANNING_ONLY" in design and "NOT_CONFIRMATORY_ELIGIBLE" in design
    registry = json.loads(
        (ROOT / "registry/icml2027/sharper_boundary_candidates.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry["canonical_baseline"]["status"] == "VERIFIED_CONFIRMATORY_ELIGIBLE"
    assert registry["canonical_baseline"]["frozen_study_modified"] is False
    assert registry["best_verified_sharper_result"] == "NONE_IMPLEMENTED_OR_CONFIRMATORY_ELIGIBLE"
    assert all(
        row["implementation_status"]
        in {
            "VERIFIED_CONFIRMATORY_ELIGIBLE",
            "VERIFIED_DIAGNOSTIC_ONLY",
            "IMPLEMENTED_NOT_VERIFIED",
            "NOT_IMPLEMENTED",
        }
        and not row["confirmatory_eligibility"]
        for row in registry["candidates"]
    )
