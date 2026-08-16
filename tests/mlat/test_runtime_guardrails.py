import asyncio

import pytest

from mlat_reference.ingest.client import CKBReceiverNetworkClient, NetworkConfig
from ckb_registry.discovery import CKBConfig, CKBPeerDiscovery
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


def test_ckb_discovery_never_hides_rpc_failure(monkeypatch):
    discovery = CKBPeerDiscovery(
        CKBConfig(
            receiver_registry_type_hash="0x" + "12" * 32,
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
