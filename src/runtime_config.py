"""Shared runtime configuration loading for MLAT entrypoints."""

from __future__ import annotations

from dataclasses import dataclass
import os

from network.ckb_client import NetworkConfig


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class RuntimeSettings:
    """Environment-derived runtime settings."""

    network_config: NetworkConfig
    db_path: str


def load_runtime_settings(
    *,
    max_receivers_default: int,
    db_path_default: str = "mlat_data.db",
) -> RuntimeSettings:
    """Load shared network and storage settings from environment."""
    fourdsky_endpoint = os.getenv("FOURDSKYENDPOINT") or os.getenv("FOURDSKY_ENDPOINT", "")
    fourdsky_api_key = os.getenv("FOURDSKYAPIKEY") or os.getenv("FOURDSKY_API_KEY")

    config = NetworkConfig(
        ckb_network=os.getenv("CKB_NETWORK", "testnet"),
        ckb_rpc_url=os.getenv("CKB_RPC_URL", "https://testnet.ckb.dev/rpc"),
        ckb_indexer_url=os.getenv("CKB_INDEXER_URL", "https://testnet.ckb.dev/indexer"),
        receiver_registry_type_hash=os.getenv("RECEIVER_REGISTRY_TYPE_HASH", ""),
        api_key=fourdsky_api_key,
        fourdskyendpoint=fourdsky_endpoint,
        fourdsky_transport=os.getenv("FOURDSKY_TRANSPORT", "auto"),
        fourdsky_auth_header=os.getenv("FOURDSKY_AUTH_HEADER", "X-API-Key"),
        fourdsky_auth_scheme=os.getenv("FOURDSKY_AUTH_SCHEME") or None,
        fourdsky_auth_token=os.getenv("FOURDSKY_AUTH_TOKEN") or None,
        fourdsky_subscribe_message=os.getenv("FOURDSKY_SUBSCRIBE_MESSAGE") or None,
        fourdsky_bridge_command=os.getenv("FOURDSKY_BRIDGE_COMMAND") or None,
        max_receivers=int(os.getenv("MAX_RECEIVERS", str(max_receivers_default))),
        simulate_if_unavailable=env_bool("SIMULATE_IF_UNAVAILABLE", True),
    )
    db_path = os.getenv("DATABASE_PATH", db_path_default)
    return RuntimeSettings(network_config=config, db_path=db_path)
