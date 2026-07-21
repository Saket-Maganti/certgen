"""Independent dependency and model-asset network policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class NetworkMode(str, Enum):
    ONLINE_DEPENDENCIES_ONLINE_ASSETS = "ONLINE_DEPENDENCIES_ONLINE_ASSETS"
    ONLINE_DEPENDENCIES_OFFLINE_ASSETS = "ONLINE_DEPENDENCIES_OFFLINE_ASSETS"
    OFFLINE_DEPENDENCIES_OFFLINE_ASSETS = "OFFLINE_DEPENDENCIES_OFFLINE_ASSETS"


@dataclass(frozen=True)
class NetworkPolicy:
    mode: NetworkMode
    dependency_network_allowed: bool
    model_asset_network_allowed: bool
    wheelhouse: str | None = None

    def validate(self) -> None:
        expected = {
            NetworkMode.ONLINE_DEPENDENCIES_ONLINE_ASSETS: (True, True),
            NetworkMode.ONLINE_DEPENDENCIES_OFFLINE_ASSETS: (True, False),
            NetworkMode.OFFLINE_DEPENDENCIES_OFFLINE_ASSETS: (False, False),
        }[self.mode]
        observed = (self.dependency_network_allowed, self.model_asset_network_allowed)
        if observed != expected:
            raise ValueError(f"network flags {observed} contradict mode {self.mode.value}")
        if not self.dependency_network_allowed and self.wheelhouse is not None:
            root = Path(self.wheelhouse)
            if not root.is_dir() or not any(root.glob("*.whl")):
                raise FileNotFoundError("offline dependency mode declares an unusable wheelhouse")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload.pop("mode", None)
        return {**payload, "network_mode": self.mode.value, "claim_allowed": False}


def network_policy_from_config(config: Mapping[str, Any]) -> NetworkPolicy:
    if "dependency_network_allowed" not in config or "model_asset_network_allowed" not in config:
        raise ValueError("configuration must separate dependency_network_allowed and model_asset_network_allowed")
    policy = NetworkPolicy(
        NetworkMode(str(config["network_mode"])),
        bool(config["dependency_network_allowed"]),
        bool(config["model_asset_network_allowed"]),
        str(config["wheelhouse"]) if config.get("wheelhouse") else None,
    )
    policy.validate()
    return policy
