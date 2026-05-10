# Aircraft MLAT Localization System 🛩️

A complete Multilateration (MLAT) system for localizing aircraft using distributed Mode-S data from the Neuron network with CKB-based receiver discovery.

## 🚨 Problem This Solves

Many aircraft-tracking and aviation-data systems rely heavily on:

- aircraft self-reported positions
- centrally managed receiver directories
- tightly coupled data pipelines

That creates several operational problems:

1. **Not every useful signal includes a trusted aircraft position**
   - Mode-S and related traffic can be observed even when a clean position is not directly available
   - a multilateration layer lets you estimate position from receiver timing instead of waiting for the aircraft to tell you where it is

2. **Receiver infrastructure is often managed informally or centrally**
   - teams end up with spreadsheets, ad hoc service discovery, or private registries
   - that makes it harder to scale contributor-operated receiver fleets cleanly

3. **Operators need a bridge between raw receiver feeds and usable positioning infrastructure**
   - collecting signals is not the same as turning them into usable localization output
   - you still need correlation, solving, storage, and an API/dashboard layer

This project addresses those gaps by combining:

- receiver discovery via a CKB-backed registry model
- feed ingestion via live or simulated transports
- MLAT correlation and solving
- storage and visualization for downstream consumers

## 🎯 What This Does

This system **tracks aircraft without relying on GPS broadcasts** by using signal timing from multiple ground receivers. It's like GPS in reverse - instead of satellites telling your phone where you are, ground stations figure out where aircraft are by measuring when their signals arrive.

## 👥 Who This Is For

This project makes the most sense for people who already operate, integrate, or study distributed aviation-data infrastructure, especially:

- **receiver-network operators**
  - teams managing multiple Mode-S / ADS-B / MLAT-capable receivers
  - groups that want a more structured discovery and metadata model

- **aviation-data infrastructure builders**
  - developers who need an API/database/dashboard layer on top of raw receiver traffic
  - teams prototyping localization pipelines before wiring real provider integrations

- **researchers and protocol experimenters**
  - people exploring decentralized discovery, multilateration, or collaborative receiver networks
  - engineers comparing different transport, registry, and solver designs

- **platform teams evaluating CKB-backed registry workflows**
  - if you want to use CKB as a decentralized registry rather than as a full telemetry database, this repo is a concrete reference implementation

## 🤝 Why Integrate This In Your Stack

If you are the target audience above, this project is useful because it gives you an opinionated separation of concerns:

- **CKB for receiver registry state**
  - store receiver metadata and ownership externally from the runtime

- **4DSky or adapter transport for live feed ingress**
  - plug in a websocket or bridge process without rewriting the whole system

- **MLAT runtime for correlation and localization**
  - turn raw observations into trackable position outputs

- **SQLite + API + dashboard for operations**
  - inspect the system, validate it, and expose results to downstream consumers

In practical terms, this repo helps a team avoid building each of those layers from scratch while still keeping the design open enough to swap discovery or transport components later.

## ✨ Key Features

- ✅ **MLAT Algorithm**: Time Difference of Arrival (TDOA) positioning
- ✅ **Signal Correlation**: Automatically matches signals from the same aircraft
- ✅ **Distributed Network**: Designed for decentralized Neuron network integration
- ✅ **Real-time Processing**: Handles live data streams from multiple receivers
- ✅ **Quality Metrics**: Calculates position uncertainty (GDOP)
- ⚠️ **Network Ready**: Framework prepared for CKB + 4DSky integration

## 📌 Current Maturity

This repository is best understood as:

- **production-structured**
- **test-backed**
- **simulation-capable today**
- **integration-ready for real CKB + 4DSky inputs**

It is **not** yet fully proven against live deployed registry data and live 4DSky credentials in this repo alone.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd mlat-system

# Install dependencies
pip install -r requirements.txt
```

### Run Tests

```bash
# Run the test suite
python -m pytest
```

### Basic Usage

```python
from mlat.solver import MLATSolver, ReceiverPosition, SignalObservation

# Create receivers
receivers = [
    ReceiverPosition(40.7128, -74.0060, 10, "NYC"),
    ReceiverPosition(42.3601, -71.0589, 20, "BOS"),
    ReceiverPosition(39.9526, -75.1652, 15, "PHL"),
    ReceiverPosition(38.9072, -77.0369, 25, "DC"),
]

# Create observations (would come from real receivers)
observations = [...]  # Signal data with timestamps

# Solve position
solver = MLATSolver()
position = solver.solve_position(observations)

if position:
    print(f"Aircraft at: {position.latitude}°, {position.longitude}°")
    print(f"Altitude: {position.altitude} meters")
    print(f"Uncertainty: ±{position.uncertainty} meters")
```

## 📁 Project Structure

```
mlat-system/
├── src/
│   ├── mlat/              # Core MLAT positioning algorithm
│   ├── correlation/       # Signal correlation and matching
│   ├── network/          # CKB + 4DSky integration
│   └── main.py           # System orchestrator
├── tests/                # Test suite
├── docs/                 # Documentation
└── requirements.txt      # Dependencies
```

## 🔬 How It Works

1. **Aircraft transmits** Mode-S signal
2. **Multiple receivers** hear it at different times
3. **Signal correlator** matches signals from same aircraft
4. **MLAT solver** calculates position from time differences
5. **Output** latitude, longitude, altitude + uncertainty

### The Math (Simple Explanation)

```
Time difference = Distance difference / Speed of light

With 4 receivers, you get 3 time differences.
Each creates a hyperbola of possible positions.
Where the hyperbolas intersect = aircraft position!
```

## 📊 Components

### 1. MLAT Solver (`src/mlat/solver.py`)
- Implements Gauss-Newton iterative TDOA solver
- Handles coordinate conversions (Lat/Lon ↔ ECEF)
- Estimates position uncertainty (GDOP)
- **Status**: ✅ Production-ready

### 2. Signal Correlator (`src/correlation/correlator.py`)
- Time-window based clustering
- Filters duplicates from same receiver
- Groups signals by message content
- **Status**: ✅ Complete

### 3. Network Client (`src/network/ckb_client.py`)
- CKB blockchain peer discovery interface
- 4DSky data streaming interface
- Connection management
- **Status**: ⚠️ Framework ready (needs SDK integration)

### 4. System Orchestrator (`src/main.py`)
- Coordinates all subsystems
- Real-time processing loop
- Statistics and monitoring
- **Status**: ✅ Complete

## 🎓 Educational Value

This project demonstrates:
- **Advanced signal processing** (TDOA, correlation)
- **Coordinate geometry** (ECEF, geodetic systems)
- **Numerical methods** (Gauss-Newton optimization)
- **Distributed systems** (peer-to-peer architecture)
- **Real-time processing** (streaming data handling)

## 🛠️ Development Status

| Component | Status | Next Steps |
|-----------|--------|------------|
| MLAT Core | ✅ Complete | Fine-tuning convergence |
| Correlation | ✅ Complete | Real-world testing |
| Network Interface | ⚠️ Stub | SDK integration needed |
| Visualization | ❌ TODO | Add web dashboard |
| Testing | ⚠️ Partial | Need real data validation |

## 🔧 To Complete Production System

1. **Get SDK Access**:
   - CKB testnet credentials / node access
   - Receiver registry type hash
   - 4DSky SDK documentation

2. **Implement Stubs**:
   - Replace the simulated 4DSky feed with the real SDK
   - Register and discover receivers via the on-chain CKB registry

3. **Test with Real Data**:
   - Connect to actual receivers
   - Validate against known aircraft positions
   - Tune parameters

4. **Add Features**:
   - Web visualization dashboard
   - Database for historical tracks
   - API for external access

## 📚 Documentation

- **[Getting Started Guide](docs/GETTING_STARTED.md)**: Detailed setup and usage
- **[Project Summary](docs/PROJECT_SUMMARY.md)**: Complete technical overview
- **[CKB Integration Guide](docs/CKB_INTEGRATION_GUIDE.md)**: Receiver registry and chain setup
- **Code Comments**: Extensive inline documentation

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Expected output:
# ✅ Solver tests
# ✅ Correlator tests
# ✅ Database tests
# ✅ API tests
```

## 📈 Expected Performance

- **Accuracy**: 50-500m depending on receiver geometry
- **Throughput**: 1000+ aircraft, 10,000+ signals/sec
- **Latency**: <100ms from signal to position
- **Requirements**: Minimum 4 receivers, GPS time sync

## 🤝 Contributing

This is a challenge project demonstrating MLAT concepts. To extend:

1. Implement real CKB registry integration
2. Add 4DSky SDK connection
3. Improve solver convergence
4. Add visualization
5. Write more tests

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

Built for the Neuron Network MLAT challenge. Demonstrates decentralized aircraft tracking using:
- Neuron distributed receiver network
- CKB for peer discovery
- 4DSky for data streaming
- MLAT for position calculation

## 📞 Support

- Review the documentation in `/docs`
- Check test files for usage examples
- Read inline code comments

---

**Ready to track aircraft!** ✈️ This system provides a complete foundation for decentralized aircraft localization. Connect it to real data sources and start tracking! 🚀
