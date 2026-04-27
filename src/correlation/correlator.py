"""
Signal Correlation Module

Matches Mode-S messages from different receivers that belong to the same
aircraft transmission. This is crucial because the same signal arrives
at different receivers at different times.
"""

from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import time


@dataclass
class RawSignal:
    """Raw Mode-S signal from a receiver"""
    receiver_id: str
    timestamp: float  # GPS time in seconds
    message: str      # Mode-S message (hex string)
    signal_strength: float = 0.0  # Optional: RSSI


@dataclass
class CorrelatedSignalGroup:
    """A group of signals that came from the same aircraft transmission"""
    message: str  # The Mode-S message content
    signals: List[RawSignal]
    first_timestamp: float
    time_span: float  # Time from first to last reception
    
    def __post_init__(self):
        self.signals.sort(key=lambda x: x.timestamp)
        if len(self.signals) > 0:
            self.first_timestamp = self.signals[0].timestamp
            self.time_span = self.signals[-1].timestamp - self.signals[0].timestamp


class SignalCorrelator:
    """
    Correlates signals from multiple receivers to identify which signals
    came from the same aircraft transmission.
    
    Algorithm:
    1. Group signals by message content (same message = same transmission)
    2. Within each message group, cluster by time proximity
    3. Only keep groups with signals from multiple receivers
    """
    
    def __init__(
        self,
        time_window: float = 0.001,  # 1 millisecond window
        min_receivers: int = 4,
        buffer_duration: float = 2.0  # Keep signals for 2 seconds
    ):
        """
        Initialize correlator.
        
        Args:
            time_window: Maximum time difference for signals to be correlated (seconds)
            min_receivers: Minimum receivers needed for valid correlation
            buffer_duration: How long to buffer signals before discarding
        """
        self.time_window = time_window
        self.min_receivers = min_receivers
        self.buffer_duration = buffer_duration
        
        # Buffer to store incoming signals
        self.signal_buffer: List[RawSignal] = []
        
        # Track which messages we've already processed
        self.processed_groups: Set[str] = set()
    
    def add_signal(self, signal: RawSignal) -> None:
        """Add a new signal to the buffer"""
        self.signal_buffer.append(signal)
        self._cleanup_old_signals()
    
    def add_signals(self, signals: List[RawSignal]) -> None:
        """Add multiple signals at once"""
        self.signal_buffer.extend(signals)
        self._cleanup_old_signals()
    
    def _cleanup_old_signals(self) -> None:
        """Remove signals older than buffer_duration"""
        if not self.signal_buffer:
            return
        
        current_time = time.time()
        self.signal_buffer = [
            sig for sig in self.signal_buffer
            if (current_time - sig.timestamp) < self.buffer_duration
        ]
    
    def correlate(self) -> List[CorrelatedSignalGroup]:
        """
        Find groups of correlated signals in the buffer.
        
        Returns:
            List of signal groups that can be used for MLAT
        """
        if len(self.signal_buffer) < self.min_receivers:
            return []
        
        # Group signals by message content
        message_groups = defaultdict(list)
        for signal in self.signal_buffer:
            message_groups[signal.message].append(signal)
        
        correlated_groups = []
        
        # For each unique message, find temporal clusters
        for message, signals in message_groups.items():
            if len(signals) < self.min_receivers:
                continue
            
            # Sort by timestamp
            signals.sort(key=lambda x: x.timestamp)
            
            # Cluster signals within time window
            clusters = self._cluster_by_time(signals)
            
            # Create correlated groups from valid clusters
            for cluster in clusters:
                if self._is_valid_cluster(cluster):
                    group = CorrelatedSignalGroup(
                        message=message,
                        signals=cluster,
                        first_timestamp=cluster[0].timestamp,
                        time_span=0.0  # Will be calculated in __post_init__
                    )
                    
                    # Create unique ID for this group
                    group_id = f"{message}_{group.first_timestamp:.6f}"
                    
                    # Only add if not already processed
                    if group_id not in self.processed_groups:
                        correlated_groups.append(group)
                        self.processed_groups.add(group_id)
        
        return correlated_groups
    
    def _cluster_by_time(self, signals: List[RawSignal]) -> List[List[RawSignal]]:
        """
        Cluster signals that are close in time.
        
        Uses a sliding window approach to group signals.
        """
        if not signals:
            return []
        
        clusters = []
        current_cluster = [signals[0]]
        
        for signal in signals[1:]:
            time_diff = signal.timestamp - current_cluster[0].timestamp
            
            if time_diff <= self.time_window:
                # Add to current cluster
                current_cluster.append(signal)
            else:
                # Start new cluster
                if len(current_cluster) >= self.min_receivers:
                    clusters.append(current_cluster)
                current_cluster = [signal]
        
        # Don't forget the last cluster
        if len(current_cluster) >= self.min_receivers:
            clusters.append(current_cluster)
        
        return clusters
    
    def _is_valid_cluster(self, signals: List[RawSignal]) -> bool:
        """
        Check if a cluster is valid for MLAT.
        
        Requirements:
        - At least min_receivers signals
        - Signals from different receivers (not duplicates)
        - Time span is reasonable
        """
        if len(signals) < self.min_receivers:
            return False
        
        # Check for unique receivers
        receiver_ids = set(sig.receiver_id for sig in signals)
        if len(receiver_ids) < self.min_receivers:
            return False  # Duplicates from same receiver
        
        # Check time span is reasonable (signals should arrive within ~10ms max)
        time_span = signals[-1].timestamp - signals[0].timestamp
        if time_span > 0.010:  # 10 milliseconds
            return False
        
        return True
    
    def get_statistics(self) -> Dict:
        """Get statistics about the correlation process"""
        message_counts = defaultdict(int)
        for signal in self.signal_buffer:
            message_counts[signal.message] += 1
        
        return {
            "buffer_size": len(self.signal_buffer),
            "unique_messages": len(message_counts),
            "processed_groups": len(self.processed_groups),
            "avg_signals_per_message": (
                sum(message_counts.values()) / len(message_counts)
                if message_counts else 0
            )
        }


class ModeSDecoder:
    """
    Basic Mode-S message decoder to extract useful information.
    
    Mode-S messages contain:
    - ICAO address (unique aircraft ID)
    - Message type
    - Data payload
    """
    
    @staticmethod
    def get_icao_address(message: str) -> str:
        """
        Extract ICAO aircraft address from Mode-S message.
        
        For DF17 (ADS-B) messages, ICAO is in bits 9-32
        """
        if len(message) < 8:
            return "UNKNOWN"
        
        # Convert hex to binary
        try:
            binary = bin(int(message[:2], 16))[2:].zfill(8)
            df = int(binary[:5], 2)  # Downlink Format
            
            # DF 17, 18 are ADS-B messages
            if df in [17, 18]:
                icao = message[2:8]
                return icao.upper()
            else:
                # For other formats, ICAO might be in different positions
                return message[2:8].upper()  # Approximation
        except:
            return "UNKNOWN"
    
    @staticmethod
    def get_message_type(message: str) -> int:
        """Get the message type code"""
        try:
            binary = bin(int(message[:2], 16))[2:].zfill(8)
            df = int(binary[:5], 2)
            return df
        except:
            return -1


# Example usage
if __name__ == "__main__":
    # Simulate incoming signals from 4 receivers
    correlator = SignalCorrelator(time_window=0.002, min_receivers=4)
    
    # Aircraft transmits message at t=100.000000
    # Different receivers hear it at slightly different times
    
    base_time = 100.0
    message = "8D4840D6202CC371C32CE0576098"
    
    # Simulate signals arriving at different receivers
    signals = [
        RawSignal("RECV_1", base_time + 0.000100, message, 45.0),
        RawSignal("RECV_2", base_time + 0.000300, message, 42.0),
        RawSignal("RECV_3", base_time + 0.000200, message, 48.0),
        RawSignal("RECV_4", base_time + 0.000500, message, 38.0),
        RawSignal("RECV_5", base_time + 0.000150, message, 44.0),
    ]
    
    # Add signals to correlator
    correlator.add_signals(signals)
    
    # Find correlated groups
    groups = correlator.correlate()
    
    print(f"Found {len(groups)} correlated signal groups")
    
    for i, group in enumerate(groups):
        print(f"\nGroup {i+1}:")
        print(f"  Message: {group.message}")
        print(f"  ICAO: {ModeSDecoder.get_icao_address(group.message)}")
        print(f"  Receivers: {len(group.signals)}")
        print(f"  Time span: {group.time_span*1000:.3f} ms")
        print(f"  Receivers: {[sig.receiver_id for sig in group.signals]}")
    
    # Show statistics
    stats = correlator.get_statistics()
    print(f"\nCorrelator Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
