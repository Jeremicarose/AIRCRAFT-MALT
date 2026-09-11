import asyncio

import pytest

from mlat_reference.ingest.client import CKBReceiverNetworkClient, NetworkConfig
from ckb_registry.discovery import CKBConfig, CKBPeerDiscovery, ReceiverInfo
from mlat_reference.runtime import validate_startup_constraints
from mlat_reference.config import load_runtime_settings


def test_strict_production_rejects_simulation_transport(monkeypatch):
    monkeypatch.setenv("STRICT_PRODUCTION_MODE", "true")
    monkeypatch.setenv("FOURDSKY_TRANSPORT", "simulation")
    monkeypatch.setenv("SIMULATE_IF_UNAVAILABLE", "false")
    monkeypatch.setenv("DEMO_MODE", "false")

    with pytest.raises(ValueError, match="FOURDSKY_TRANSPORT=simulation"):
        load_runtime_settings(max_receivers_default=10)


def test_strict_production_rejects_simulate_if_unavailable(monkeypatch):
    monkeypatch.setenv("STRICT_PRODUCTION_MODE", "true")
    monkeypatch.setenv("FOURDSKY_TRANSPORT", "command-jsonl")
    monkeypatch.setenv("SIMULATE_IF_UNAVAILABLE", "true")
    monkeypatch.setenv("DEMO_MODE", "false")

    with pytest.raises(ValueError, match="SIMULATE_IF_UNAVAILABLE=true"):
        load_runtime_settings(max_receivers_default=10)


def test_strict_production_rejects_auto_transport(monkeypatch):
    monkeypatch.setenv("STRICT_PRODUCTION_MODE", "true")
    monkeypatch.setenv("FOURDSKY_TRANSPORT", "auto")
    monkeypatch.setenv("SIMULATE_IF_UNAVAILABLE", "false")
    monkeypatch.setenv("DEMO_MODE", "false")

    with pytest.raises(ValueError, match="FOURDSKY_TRANSPORT=auto"):
        load_runtime_settings(max_receivers_default=10)


def test_strict_production_rejects_demo_mode(monkeypatch):
    monkeypatch.setenv("STRICT_PRODUCTION_MODE", "true")
    monkeypatch.setenv("FOURDSKY_TRANSPORT", "command-jsonl")
    monkeypatch.setenv("SIMULATE_IF_UNAVAILABLE", "false")
    monkeypatch.setenv("DEMO_MODE", "true")

    with pytest.raises(ValueError, match="DEMO_MODE=true"):
        load_runtime_settings(max_receivers_default=10)


def test_historical_registry_defaults_to_its_type_hash_binding(monkeypatch):
    monkeypatch.setenv("RECEIVER_REGISTRY_TYPE_HASH", "0x" + "12" * 32)
    monkeypatch.delenv("RECEIVER_REGISTRY_HASH_TYPE", raising=False)

    settings = load_runtime_settings(max_receivers_default=10)

    assert settings.network_config.receiver_registry_hash_type == "type"


def test_strict_production_accepts_explicit_data1_registry_binding(monkeypatch):
    monkeypatch.setenv("STRICT_PRODUCTION_MODE", "true")
    monkeypatch.setenv("FOURDSKY_TRANSPORT", "command-jsonl")
    monkeypatch.setenv("SIMULATE_IF_UNAVAILABLE", "false")
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("RECEIVER_REGISTRY_TYPE_HASH", "0x" + "12" * 32)
    monkeypatch.setenv("RECEIVER_REGISTRY_HASH_TYPE", "data1")
    monkeypatch.setenv("CKB_SSL_VERIFY", "true")

    settings = load_runtime_settings(max_receivers_default=10)

    assert settings.network_config.receiver_registry_hash_type == "data1"


def test_strict_production_rejects_mutable_type_hash_registry_binding(monkeypatch):
    monkeypatch.setenv("STRICT_PRODUCTION_MODE", "true")
    monkeypatch.setenv("FOURDSKY_TRANSPORT", "command-jsonl")
    monkeypatch.setenv("SIMULATE_IF_UNAVAILABLE", "false")
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("RECEIVER_REGISTRY_TYPE_HASH", "0x" + "12" * 32)
    monkeypatch.setenv("RECEIVER_REGISTRY_HASH_TYPE", "type")
    monkeypatch.setenv("ALLOW_MUTABLE_REGISTRY_CODE", "true")

    with pytest.raises(ValueError, match="mutable contract code"):
        load_runtime_settings(max_receivers_default=10)


def test_strict_production_rejects_disabled_ckb_tls_verification(monkeypatch):
    monkeypatch.setenv("STRICT_PRODUCTION_MODE", "true")
    monkeypatch.setenv("FOURDSKY_TRANSPORT", "command-jsonl")
    monkeypatch.setenv("SIMULATE_IF_UNAVAILABLE", "false")
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("CKB_SSL_VERIFY", "false")

    with pytest.raises(ValueError, match="CKB_SSL_VERIFY=false"):
        load_runtime_settings(max_receivers_default=10)


def test_ckb_discovery_never_hides_rpc_failure(monkeypatch):
    discovery = CKBPeerDiscovery(
        CKBConfig(
            receiver_registry_type_hash="0x" + "12" * 32,
            receiver_registry_hash_type="data1",
        )
    )

    async def fail_tip():
        raise RuntimeError("ckb unavailable")

    monkeypatch.setattr(discovery, "_get_tip_block_number", fail_tip)

    with pytest.raises(RuntimeError, match="ckb unavailable"):
        asyncio.run(discovery.initialize())


def test_transport_selection_does_not_fallback_to_simulation_in_strict_mode():
    client = CKBReceiverNetworkClient(
        NetworkConfig(
            fourdsky_transport="auto",
            strict_production_mode=True,
            simulate_if_unavailable=False,
        )
    )

    with pytest.raises(RuntimeError, match="FOURDSKY_TRANSPORT=auto"):
        client._determine_transport()


def test_validate_startup_constraints_allows_non_strict_simulation(monkeypatch):
    monkeypatch.setenv("STRICT_PRODUCTION_MODE", "false")
    monkeypatch.setenv("FOURDSKY_TRANSPORT", "simulation")
    monkeypatch.setenv("SIMULATE_IF_UNAVAILABLE", "true")
    monkeypatch.setenv("DEMO_MODE", "true")

    settings = load_runtime_settings(max_receivers_default=10)

    validate_startup_constraints(settings)
    assert settings.strict_production_mode is False


def test_runtime_loads_clock_uncertainty_threshold(monkeypatch):
    monkeypatch.setenv("STRICT_PRODUCTION_MODE", "false")
    monkeypatch.setenv("MAX_CLOCK_UNCERTAINTY_NS", "75")

    settings = load_runtime_settings(max_receivers_default=10)

    assert settings.max_clock_uncertainty_ns == 75.0


def _registry_receiver(identity_byte: str, *, updated_at: float) -> ReceiverInfo:
    identity = "0x" + identity_byte * 64
    return ReceiverInfo(
        receiver_id=f"RECEIVER_{identity_byte.upper()}",
        receiver_identity=identity,
        data_source="ckb_registry",
        latitude=1.0,
        longitude=36.0,
        altitude=1_700.0,
        status="online",
        last_seen=updated_at,
        capabilities=["mode-s", "mlat"],
        ckb_address="0xowner",
        lock_hash="0xlock",
        metadata={"sequence": int(updated_at)},
    )


def test_receiver_capacity_selection_is_stable_by_identity_not_timestamp():
    client = CKBReceiverNetworkClient(
        NetworkConfig(max_receivers=1, fourdsky_transport="command-jsonl")
    )
    older_lower_identity = _registry_receiver("1", updated_at=1.0)
    newer_higher_identity = _registry_receiver("f", updated_at=9_999.0)

    selected = client._select_receivers([newer_higher_identity, older_lower_identity])

    assert [receiver.receiver_identity for receiver in selected] == [
        older_lower_identity.receiver_identity
    ]


def test_registry_refresh_removes_identity_no_longer_discovered(monkeypatch):
    client = CKBReceiverNetworkClient(
        NetworkConfig(
            receiver_registry_type_hash="0x" + "4" * 64,
            fourdsky_transport="command-jsonl",
        )
    )
    removed = _registry_receiver("1", updated_at=1.0)
    retained = _registry_receiver("2", updated_at=2.0)
    client.active_receivers.update({removed.runtime_id: removed, retained.runtime_id: retained})

    async def refreshed_receivers():
        return [retained]

    monkeypatch.setattr(client.peer_discovery, "discover_peers", refreshed_receivers)

    assert asyncio.run(client.refresh_registry_receivers()) is True
    assert set(client.active_receivers) == {retained.receiver_identity}
    assert client.registry_discovery_live is True


def test_failed_registry_refresh_removes_unverifiable_registry_receivers(monkeypatch):
    client = CKBReceiverNetworkClient(
        NetworkConfig(
            receiver_registry_type_hash="0x" + "4" * 64,
            fourdsky_transport="command-jsonl",
        )
    )
    receiver = _registry_receiver("1", updated_at=1.0)
    client.active_receivers[receiver.runtime_id] = receiver

    async def failed_refresh():
        raise RuntimeError("CKB indexer unavailable")

    monkeypatch.setattr(client.peer_discovery, "discover_peers", failed_refresh)

    with pytest.raises(RuntimeError, match="CKB indexer unavailable"):
        asyncio.run(client.refresh_registry_receivers())

    assert client.active_receivers == {}
    assert client.registry_discovery_live is False
    assert client.registry_refresh_error == "CKB indexer unavailable"
