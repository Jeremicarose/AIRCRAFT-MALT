"""Shared runtime helpers for MLAT entrypoints."""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Generic, Optional, TypeVar
import time

from mlat_reference.correlation.correlator import RawSignal, SignalCorrelator
from mlat_reference.ingest.client import CKBReceiverNetworkClient, NetworkConfig
from ckb_registry.discovery import ReceiverInfo

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
        self.network_client = CKBReceiverNetworkClient(config)
        self.correlator = SignalCorrelator(
            time_window=time_window,
            min_receivers=min_receivers,
        )
        self.receiver_positions: Dict[str, ReceiverPositionT] = {}
        self.is_running = False
        self.instrumentation = {
            "last_signal_at": 0.0,
            "last_signal_age_s": None,
            "last_receiver_id": None,
            "last_message": None,
        }
        self.ingest_latencies_ms: Deque[float] = deque(maxlen=1000)

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
        *,
        timestamp_ns: Optional[int] = None,
        clock_synchronized: bool = False,
        clock_source: str = "unknown",
        clock_uncertainty_ns: Optional[float] = None,
    ):
        """Create a raw signal and feed it into the correlator."""
        signal = RawSignal(
            receiver_id=receiver_id,
            timestamp=timestamp,
            message=message,
            signal_strength=0.0,
            timestamp_ns=timestamp_ns,
            clock_synchronized=clock_synchronized,
            clock_source=clock_source,
            clock_uncertainty_ns=clock_uncertainty_ns,
        )
        now = time.time()
        ingest_latency_ms = max(0.0, (now - timestamp) * 1000)
        self.instrumentation.update(
            {
                "last_signal_at": now,
                "last_signal_age_s": max(0.0, now - timestamp),
                "last_receiver_id": receiver_id,
                "last_message": message,
            }
        )
        self.ingest_latencies_ms.append(ingest_latency_ms)
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

    def get_runtime_instrumentation(self) -> Dict[str, object]:
        """Expose recent ingest timing for health and stats reporting."""
        latencies = list(self.ingest_latencies_ms)
        avg_ingest_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0
        max_ingest_latency_ms = max(latencies) if latencies else 0.0
        last_signal_at = float(self.instrumentation.get("last_signal_at") or 0.0)
        return {
            **self.instrumentation,
            "last_signal_age_s": (
                max(0.0, time.time() - last_signal_at) if last_signal_at else None
            ),
            "avg_ingest_latency_ms": avg_ingest_latency_ms,
            "max_ingest_latency_ms": max_ingest_latency_ms,
        }
