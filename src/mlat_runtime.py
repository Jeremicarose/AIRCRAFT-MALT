"""Shared runtime helpers for MLAT entrypoints."""

from __future__ import annotations

from typing import Dict, Generic, Optional, TypeVar

from correlation.correlator import RawSignal, SignalCorrelator
from network.ckb_client import CKBNeuronNetworkClient, NetworkConfig
from network.ckb_discovery import ReceiverInfo


ReceiverPositionT = TypeVar("ReceiverPositionT")
ObservationT = TypeVar("ObservationT")


class BaseMLATRuntime(Generic[ReceiverPositionT, ObservationT]):
    """Shared network/correlation plumbing for demo and production runtimes."""

    def __init__(
        self,
        config: NetworkConfig,
        *,
        time_window: float,
        min_receivers: int,
    ):
        self.config = config
        self.network_client = CKBNeuronNetworkClient(config)
        self.correlator = SignalCorrelator(
            time_window=time_window,
            min_receivers=min_receivers,
        )
        self.receiver_positions: Dict[str, ReceiverPositionT] = {}
        self.is_running = False

    async def initialize_network(self):
        """Initialize discovery/streaming inputs and cache receiver geometry."""
        await self.network_client.initialize()
        self._cache_receiver_positions()

    def _cache_receiver_positions(self):
        for receiver_id, info in self.network_client.active_receivers.items():
            receiver_position = self.build_receiver_position(receiver_id, info)
            self.receiver_positions[receiver_id] = receiver_position
            self.on_receiver_cached(receiver_id, info)

    def build_receiver_position(
        self,
        receiver_id: str,
        info: ReceiverInfo,
    ) -> ReceiverPositionT:
        raise NotImplementedError

    def build_observation(
        self,
        signal: RawSignal,
        receiver_position: ReceiverPositionT,
    ) -> ObservationT:
        raise NotImplementedError

    def on_receiver_cached(self, receiver_id: str, info: ReceiverInfo):
        """Hook for subclasses that persist or log receiver metadata."""

    def on_signal_received(self, signal: RawSignal):
        """Hook for subclasses that track runtime counters."""

    async def handle_incoming_signal(
        self,
        receiver_id: str,
        timestamp: float,
        message: str,
    ):
        """Create a raw signal and feed it into the correlator."""
        signal = RawSignal(
            receiver_id=receiver_id,
            timestamp=timestamp,
            message=message,
            signal_strength=0.0,
        )
        self.on_signal_received(signal)
        self.correlator.add_signal(signal)

    def build_observations_from_group(self, group) -> list[ObservationT]:
        """Convert a correlated group into solver observation objects."""
        observations: list[ObservationT] = []
        for signal in group.signals:
            receiver_position = self.receiver_positions.get(signal.receiver_id)
            if receiver_position is None:
                continue
            observations.append(self.build_observation(signal, receiver_position))
        return observations
