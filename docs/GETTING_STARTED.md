# Getting Started with the MLAT System

## 🎯 What You've Built

Congratulations! You've built the foundation of a Multilateration (MLAT) Aircraft Localization System. Here's what each component does:

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MLAT SYSTEM                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐       ┌──────────────┐              │
│  │   Hedera     │──────▶│   4DSky SDK  │              │
│  │ Peer Discovery│       │  Data Stream │              │
│  └──────────────┘       └──────────────┘              │
│         │                       │                       │
│         │                       ▼                       │
│         │              ┌─────────────────┐             │
│         └─────────────▶│ Network Client  │             │
│                        └─────────────────┘             │
│                                │                        │
│                                ▼                        │
│                        ┌─────────────────┐             │
│                        │ Signal Correlator│             │
│                        └─────────────────┘             │
│                                │                        │
│                                ▼                        │
│                        ┌─────────────────┐             │
│                        │  MLAT Solver    │             │
│                        └─────────────────┘             │
│                                │                        │
│                                ▼                        │
│                        ┌─────────────────┐             │
│                        │ Aircraft Positions│            │
│                        └─────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
mlat-system/
├── README.md                      # Project overview
├── src/
│   ├── mlat/
│   │   └── solver.py             # MLAT position solver
│   ├── correlation/
│   │   └── correlator.py         # Signal correlation
│   ├── network/
│   │   └── neuron_client.py      # Network interface
│   └── main.py                    # Main orchestrator
├── tests/
│   └── test_system.py            # Test suite
└── docs/
    └── GETTING_STARTED.md        # This file
```

## 🔧 Components Explained

### 1. MLAT Solver (`src/mlat/solver.py`)

**What it does**: Calculates aircraft 3D position from time-of-arrival measurements

**Key algorithm**: Gauss-Newton iterative solver for TDOA equations

**Input**: 
- List of signal observations from multiple receivers
- Each observation has: receiver position, timestamp, signal data

**Output**:
- Aircraft latitude, longitude, altitude
- Position uncertainty estimate
- Quality metrics

**How it works**:
```python
# Example usage
solver = MLATSolver()
position = solver.solve_position(observations)

if position:
    print(f"Aircraft at: {position.latitude}, {position.longitude}")
    print(f"Altitude: {position.altitude} meters")
    print(f"Uncertainty: ±{position.uncertainty} meters")
```

### 2. Signal Correlator (`src/correlation/correlator.py`)

**What it does**: Matches signals from different receivers that came from the same aircraft

**Key features**:
- Time-window based clustering
- Duplicate filtering
- Message grouping

**How it works**:
```python
correlator = SignalCorrelator(time_window=0.002)

# Add incoming signals
correlator.add_signal(signal)

# Get correlated groups
groups = correlator.correlate()

for group in groups:
    # Each group contains signals from same transmission
    print(f"Found {len(group.signals)} receivers heard this")
```

### 3. Network Client (`src/network/neuron_client.py`)

**What it does**: Connects to the Neuron network to receive Mode-S data

**Key features**:
- Hedera-based peer discovery
- 4DSky SDK integration (stub)
- Real-time data streaming

**TODO for production**:
- Implement actual Hedera SDK calls
- Integrate real 4DSky SDK
- Handle authentication and rate limiting

## 🚀 Next Steps to Complete the System

### Step 1: Integrate Real Hedera SDK

You'll need to:
1. Install Hedera SDK: `pip install hedera-sdk-python`
2. Get Hedera testnet credentials
3. Replace the stub in `HederaPeerDiscovery.discover_peers()`

Example:
```python
from hedera import Client, TopicMessageQuery

async def discover_peers(self):
    client = Client.forTestnet()
    client.setOperator(account_id, private_key)
    
    # Query the receiver registry topic
    query = TopicMessageQuery()
    query.setTopicId(topic_id)
    
    # Parse and return receiver info
    # ...
```

### Step 2: Integrate 4DSky SDK

You'll need to:
1. Get access to 4DSky SDK documentation
2. Implement authentication
3. Replace stub in `FourDSkyDataStream`

### Step 3: Improve MLAT Algorithm

Current issues to fix:
- Initial position guess needs improvement
- Convergence criteria tuning
- Handle edge cases (coplanar receivers, etc.)

Improvements:
```python
# Better initial guess using geographic median
def _better_initial_guess(receivers):
    # Use weighted average based on time differences
    # Or use algebraic closed-form solution first
    pass

# Add robust error handling
def solve_position(self, observations):
    # Check receiver geometry (GDOP)
    if self._poor_geometry(observations):
        return None
    
    # Try multiple initial guesses
    # Pick solution with lowest residual
```

### Step 4: Add Real-Time Visualization

Create a web dashboard:

```python
# visualization/dashboard.py
import dash
from dash import html, dcc
import plotly.graph_objects as go

def create_map(positions):
    fig = go.Figure(go.Scattermapbox(
        lat=[p.latitude for p in positions],
        lon=[p.longitude for p in positions],
        mode='markers',
        marker=go.scattermapbox.Marker(size=14)
    ))
    
    fig.update_layout(mapbox_style="open-street-map")
    return fig
```

### Step 5: Add Data Persistence

Store positions for analysis:

```python
# storage/database.py
import sqlite3

class PositionDatabase:
    def store_position(self, aircraft_id, position):
        # Store in database
        pass
    
    def get_track(self, aircraft_id, start_time, end_time):
        # Retrieve historical track
        pass
```

## 🧪 Testing the System

### Manual Testing

```bash
# Run the test suite
cd mlat-system
PYTHONPATH=src python tests/test_system.py
```

### Testing with Simulated Data

The test suite includes:
- ✅ MLAT solver unit tests
- ✅ Signal correlation tests
- ✅ End-to-end pipeline tests

### Testing with Real Data

Once you integrate the SDKs:

```bash
# Run the main system
PYTHONPATH=src python src/main.py
```

## 📊 Expected Performance

### Accuracy
- **Ideal conditions**: 50-200 meter 3D accuracy
- **Good geometry**: 200-500 meters
- **Poor geometry**: 500+ meters

Factors affecting accuracy:
- Number of receivers (more = better)
- Receiver geometry (spread out = better)
- Time synchronization (GPS time critical)
- Signal quality

### Throughput
- Can process thousands of signals per second
- Depends on correlation window size
- Limited by MLAT solver iterations

## 🐛 Debugging Tips

### Common Issues

**1. No positions calculated**
- Check: Do you have 4+ receivers?
- Check: Are timestamps synchronized?
- Check: Is correlation window appropriate?

**2. Wildly incorrect positions**
- Check: Receiver positions correct?
- Check: Time synchronization
- Check: Initial guess in solver

**3. High uncertainty**
- Check: Receiver geometry (avoid clusters)
- Check: Number of receivers
- Check: Signal quality

### Debug Logging

Add detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In solver
logger.debug(f"Iteration {i}: residual = {np.linalg.norm(residuals)}")

# In correlator
logger.debug(f"Found {len(groups)} groups from {len(signals)} signals")
```

## 📚 Learning Resources

### Understanding MLAT
- "Introduction to TDOA Positioning" (papers)
- GPS and GNSS positioning textbooks
- Aviation surveillance system documentation

### Hedera
- [Hedera Documentation](https://hedera.com/docs)
- [Hedera SDK Python](https://github.com/hashgraph/hedera-sdk-py)

### Mode-S Protocol
- "The 1090MHz Riddle" (open book on Mode-S)
- ICAO Annex 10 (aviation standards)

## 🎓 Key Concepts You've Learned

1. **Time Difference of Arrival (TDOA)**: Using time differences to locate objects
2. **Hyperbolic Positioning**: Solutions form hyperbolas between receiver pairs
3. **Least Squares Optimization**: Finding best-fit solution to overdetermined system
4. **Signal Correlation**: Matching distributed observations of same event
5. **Decentralized Networks**: Peer-to-peer data sharing vs centralized
6. **Coordinate Systems**: Lat/Lon/Alt ↔ ECEF conversions

## 🌟 Future Enhancements

1. **Kalman Filtering**: Track aircraft over time, predict positions
2. **Multi-path Detection**: Handle signal reflections
3. **Velocity Estimation**: Calculate aircraft speed and heading
4. **Anomaly Detection**: Flag unusual flight patterns
5. **Network Optimization**: Dynamically select best receivers
6. **Edge Computing**: Run MLAT at receiver nodes vs central
7. **Machine Learning**: Improve correlation with learned patterns

## 🤝 Contributing

To extend this system:
1. Fork and create feature branches
2. Add tests for new functionality
3. Document your code
4. Submit pull requests

## 📞 Need Help?

- Review the inline code comments
- Check the test files for usage examples
- Read the original Mode-S protocol documentation
- Study MLAT academic papers

Good luck with your implementation! 🚀✈️
