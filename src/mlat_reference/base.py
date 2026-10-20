"""Shared runtime helpers for MLAT entrypoints."""

from __future__ import annotations

from collections import deque
from collections import Counter
import logging
import math
from typing import Any, Deque, Dict, Generic, Optional, TypeVar
import time

from mlat_reference.correlation.correlator import RawSignal, SignalCorrelator
from mlat_reference.ingest.client import CKBReceiverNetworkClient, NetworkConfig
from ckb_registry.discovery import ReceiverInfo
from mlat_reference.diagnostics import event
from mlat_reference.ingest.validation import integer_nanoseconds, mode_s_frame, clock_qualified

logger = logging.getLogger(__name__)

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
        self.instrumentation: dict[str, Any] = {
            "last_signal_at": 0.0,
            "last_signal_age_s": None,
            "last_receiver_id": None,
            "last_message": None,
        }
        self.ingest_latencies_ms: Deque[float] = deque(maxlen=1000)
        self.observation_counts: Counter[str] = Counter()
        self.observation_diagnostics: deque[dict[str, Any]] = deque(maxlen=100)
        self.receiver_last_timestamp_ns: dict[str, int] = {}
        self.receiver_registry_versions: dict[str, tuple] = {}

    def record_observation_issue(self, receiver_id: str, reason: str, disposition: str):
        self.observation_counts[disposition] += 1
        self.observation_diagnostics.append(
            {
                "receiver_id": str(receiver_id)[:128],
                "reason": reason,
                "disposition": disposition,
                "recorded_at": time.time(),
            }
        )
        event(
            logger, f"observation_{disposition}", receiver_id=str(receiver_id)[:128], reason=reason
        )

    async def initialize_network(self):
        """Initialize discovery/streaming inputs and cache receiver geometry."""
        await self.network_client.initialize()
        self._cache_receiver_positions()

    def _cache_receiver_positions(self):
        active_receiver_ids = set(self.network_client.active_receivers)
        removed_receiver_ids = set(self.receiver_positions) - active_receiver_ids
        for receiver_id in removed_receiver_ids:
            self.receiver_positions.pop(receiver_id, None)
            self.receiver_last_timestamp_ns.pop(receiver_id, None)
            self.receiver_registry_versions.pop(receiver_id, None)
        if removed_receiver_ids:
            self.on_receivers_removed(removed_receiver_ids)
        for receiver_id, info in self.network_client.active_receivers.items():
            version = (
                info.latitude,
                info.longitude,
                info.altitude,
                info.ckb_address,
                (info.metadata or {}).get("sequence"),
            )
            previous = self.receiver_registry_versions.get(receiver_id)
            if previous is not None and previous != version:
                # A new owner or location must not inherit buffered observations
                # or the previous owner's clock qualification.
                self.on_receiver_context_changed(receiver_id)
            self.receiver_registry_versions[receiver_id] = version
            receiver_position = self.build_receiver_position(receiver_id, info)
            self.receiver_positions[receiver_id] = receiver_position
            self.on_receiver_cached(receiver_id, info)
        self.on_receiver_cache_synchronized(active_receiver_ids)
        self.correlator.signal_buffer = [
            signal
            for signal in self.correlator.signal_buffer
            if signal.receiver_id in active_receiver_ids
        ]

    def on_receiver_context_changed(self, receiver_id: str):
        self.correlator.signal_buffer = [
            signal for signal in self.correlator.signal_buffer if signal.receiver_id != receiver_id
        ]

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

    def on_receivers_removed(self, receiver_ids: set[str]):
        """Hook for subclasses to remove receivers excluded by refreshed discovery."""

    def on_receiver_cache_synchronized(self, receiver_ids: set[str]):
        """Hook for subclasses to reconcile persisted inventory after discovery."""

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
        if receiver_id not in self.receiver_positions:
            # A live feed can still emit briefly after a Registry refresh.
            # Unknown or excluded identities must not reach correlation.
            self.record_observation_issue(receiver_id, "receiver_not_discovered", "rejected")
            return
        validated_message = mode_s_frame(message)
        if validated_message is None:
            self.record_observation_issue(receiver_id, "invalid_mode_s_frame", "rejected")
            return
        message = validated_message
        if timestamp_ns is not None and integer_nanoseconds(timestamp_ns) is None:
            self.record_observation_issue(receiver_id, "invalid_timestamp_ns", "rejected")
            return
        if (
            isinstance(timestamp, bool)
            or not isinstance(timestamp, (int, float))
            or not math.isfinite(timestamp)
        ):
            self.record_observation_issue(receiver_id, "invalid_timestamp", "rejected")
            return
        now = time.time()
        if (
            not now - self.config.max_observation_age_seconds
            <= timestamp
            <= now + self.config.max_observation_future_seconds
        ):
            self.record_observation_issue(receiver_id, "timestamp_outside_live_window", "rejected")
            return
        if timestamp_ns is not None and abs(timestamp - timestamp_ns / 1e9) > 0.000001:
            self.record_observation_issue(receiver_id, "timestamp_fields_disagree", "rejected")
            return
        if (
            not isinstance(clock_source, str)
            or len(clock_source) > 128
            or not isinstance(clock_synchronized, bool)
        ):
            self.record_observation_issue(receiver_id, "invalid_clock_metadata", "rejected")
            return
        if clock_uncertainty_ns is not None and (
            isinstance(clock_uncertainty_ns, bool)
            or not isinstance(clock_uncertainty_ns, (int, float))
            or not math.isfinite(clock_uncertainty_ns)
            or clock_uncertainty_ns < 0
        ):
            self.record_observation_issue(receiver_id, "invalid_clock_uncertainty", "rejected")
            return
        if timestamp_ns is not None and timestamp_ns <= self.receiver_last_timestamp_ns.get(
            receiver_id, 0
        ):
            self.record_observation_issue(
                receiver_id, "duplicate_or_out_of_order_observation", "rejected"
            )
            return
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
        qualified = (
            self._signal_clock_is_qualified(signal)
            if hasattr(self, "_signal_clock_is_qualified")
            else clock_qualified(
                clock_synchronized,
                timestamp_ns,
                clock_source,
                clock_uncertainty_ns,
                getattr(self, "max_clock_uncertainty_ns", 100),
            )
        )
        if not qualified:
            self.record_observation_issue(receiver_id, "clock_not_qualified", "quarantined")
            return
        self.observation_counts["accepted"] += 1
        if timestamp_ns is not None:
            self.receiver_last_timestamp_ns[receiver_id] = timestamp_ns
        event(logger, "observation_received", receiver_id=receiver_id, disposition="accepted")
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

    def get_runtime_instrumentation(self) -> Dict[str, Any]:
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
            "observation_counts": dict(self.observation_counts),
            "observation_diagnostics": list(self.observation_diagnostics),
        }
