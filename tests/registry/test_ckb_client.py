import asyncio

from ckb_registry.discovery import ReceiverInfo
from mlat_reference.ingest.client import CKBReceiverNetworkClient, NetworkConfig


def registry_receiver(receiver_identity: str) -> ReceiverInfo:
    return ReceiverInfo(
        receiver_id="SHARED_LABEL",
        receiver_identity=receiver_identity,
        data_source="ckb_registry",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=10.0,
        status="online",
        last_seen=1_700_000_000.0,
        capabilities=["mode-s", "mlat"],
        ckb_address="0xowner",
        lock_hash="0xlock",
    )


def test_ckb_client_preserves_distinct_type_ids_with_the_same_label():
    first_identity = "0x" + "11" * 32
    second_identity = "0x" + "22" * 32
    client = CKBReceiverNetworkClient(
        NetworkConfig(
            fourdsky_transport="command-jsonl",
            simulate_if_unavailable=False,
        )
    )

    async def fake_initialize():
        return None

    async def fake_discover():
        return [registry_receiver(first_identity), registry_receiver(second_identity)]

    client.peer_discovery.initialize = fake_initialize  # type: ignore[method-assign]
    client.peer_discovery.discover_peers = fake_discover  # type: ignore[method-assign]

    asyncio.run(client.initialize())

    assert set(client.active_receivers) == {first_identity, second_identity}
    assert {receiver.receiver_id for receiver in client.active_receivers.values()} == {
        "SHARED_LABEL"
    }


def test_ckb_client_augments_with_simulated_receivers_for_hybrid_demo():
    config = NetworkConfig(
        fourdsky_transport="simulation",
        hybrid_simulation_min_receivers=4,
    )
    client = CKBReceiverNetworkClient(config)

    client.active_receivers = {
        "runtime:RECV_NYC_001": ReceiverInfo(
            receiver_id="RECV_NYC_001",
            latitude=40.7128,
            longitude=-74.0060,
            altitude=10.0,
            status="online",
            last_seen=1_700_000_000.0,
            capabilities=["mode-s", "mlat"],
            ckb_address="ckt1real",
            lock_hash="0xreal",
            data_source="runtime",
            metadata={"source": "ckb"},
        )
    }

    client._augment_receivers_for_simulation()

    assert len(client.active_receivers) >= 4
    assert "runtime:RECV_NYC_001" in client.active_receivers
    assert any(
        receiver.metadata and receiver.metadata.get("source") == "simulation"
        for receiver in client.active_receivers.values()
    )
