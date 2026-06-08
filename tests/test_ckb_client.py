from network.ckb_client import CKBReceiverNetworkClient, NetworkConfig
from network.ckb_discovery import ReceiverInfo


def test_ckb_client_augments_with_simulated_receivers_for_hybrid_demo():
    config = NetworkConfig(
        fourdsky_transport="simulation",
        hybrid_simulation_min_receivers=4,
    )
    client = CKBReceiverNetworkClient(config)

    client.active_receivers = {
        "RECV_NYC_001": ReceiverInfo(
            receiver_id="RECV_NYC_001",
            latitude=40.7128,
            longitude=-74.0060,
            altitude=10.0,
            status="online",
            last_seen=1_700_000_000.0,
            capabilities=["mode-s", "mlat"],
            ckb_address="ckt1real",
            lock_hash="0xreal",
            metadata={"source": "ckb"},
        )
    }

    client._augment_receivers_for_simulation()

    assert len(client.active_receivers) >= 4
    assert "RECV_NYC_001" in client.active_receivers
    assert any(
        receiver.metadata and receiver.metadata.get("source") == "simulation"
        for receiver in client.active_receivers.values()
    )
