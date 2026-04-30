"""Deprecated compatibility wrapper for the legacy Hedera-era network client."""

from __future__ import annotations

import warnings

from network.ckb_client import CKBNeuronNetworkClient, NetworkConfig
from network.ckb_discovery import ReceiverInfo


class NeuronNetworkClient(CKBNeuronNetworkClient):
    """Backward-compatible alias to the CKB-based network client."""

    def __init__(self, config: NetworkConfig):
        warnings.warn(
            "network.neuron_client is deprecated. Import network.ckb_client instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(config)


class HederaPeerDiscovery:
    """Removed legacy discovery implementation."""

    def __init__(self, *_args, **_kwargs):
        raise RuntimeError(
            "Hedera discovery has been removed. Use network.ckb_discovery.CKBPeerDiscovery."
        )


class FourDSkyDataStream:
    """Removed legacy stream implementation."""

    def __init__(self, *_args, **_kwargs):
        raise RuntimeError(
            "Legacy FourDSkyDataStream has been removed. Use network.feed_transports."
        )


__all__ = ["NeuronNetworkClient", "NetworkConfig", "ReceiverInfo"]
