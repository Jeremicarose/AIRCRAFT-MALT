# Integration Guide: Connecting to Real Networks

This guide shows you how to integrate the MLAT system with actual Hedera and 4DSky networks.

## 🎯 Overview

Currently, the system uses **stub implementations** for network connectivity. To make it production-ready, you need to:

1. **Hedera Integration** - For peer discovery
2. **4DSky SDK Integration** - For Mode-S data streaming
3. **Authentication & Security** - API keys and credentials
4. **Production Configuration** - Deployment settings

## 📋 Prerequisites

### Accounts & Credentials

1. **Hedera Account**
   - Sign up at: https://portal.hedera.com/
   - Get testnet or mainnet account ID
   - Generate private keys
   - Fund account with test HBAR (for testnet)

2. **4DSky Access**
   - Contact 4DSky for SDK access
   - Obtain API credentials
   - Get SDK documentation
   - Understand data format specifications

3. **Neuron Network Registration**
   - Register as data consumer
   - Understand network topology
   - Get receiver registry topic IDs

## 🔧 Step 1: Hedera Peer Discovery Integration

### Install Hedera SDK

```bash
pip install hedera-sdk-python
```

### Implementation

Replace the stub in `src/network/neuron_client.py`:

```python
from hedera import (
    Client, 
    TopicMessageQuery, 
    TopicId,
    PrivateKey,
    AccountId
)
import json

class HederaPeerDiscovery(PeerDiscoveryInterface):
    """
    Real Hedera-based peer discovery implementation.
    """
    
    def __init__(self, config: NetworkConfig):
        self.config = config
        self.client = None
        self.topic_id = None  # Topic where receivers register
        self.cached_peers: Dict[str, ReceiverInfo] = {}
        
    async def initialize(self):
        """Initialize Hedera client"""
        # Create client for testnet or mainnet
        if self.config.hedera_network == "testnet":
            self.client = Client.forTestnet()
        else:
            self.client = Client.forMainnet()
        
        # Set operator (your account)
        account_id = AccountId.fromString(self.config.hedera_account_id)
        private_key = PrivateKey.fromString(self.config.hedera_private_key)
        self.client.setOperator(account_id, private_key)
        
        # Set the receiver registry topic
        self.topic_id = TopicId.fromString(self.config.receiver_registry_topic)
        
    async def discover_peers(self) -> List[ReceiverInfo]:
        """
        Discover active Mode-S receivers via Hedera Consensus Service.
        
        The receiver registry topic contains JSON messages like:
        {
            "receiver_id": "RECV_NYC_001",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "altitude": 10.0,
            "status": "online",
            "capabilities": ["mode-s", "adsb", "mlat"],
            "timestamp": 1234567890
        }
        """
        receivers = []
        
        # Query topic for recent messages
        query = TopicMessageQuery()
        query.setTopicId(self.topic_id)
        query.setStartTime(0)  # Or recent timestamp
        
        # Subscribe to messages
        def handle_message(message):
            try:
                data = json.loads(message.contents.decode('utf-8'))
                
                receiver = ReceiverInfo(
                    receiver_id=data['receiver_id'],
                    latitude=data['latitude'],
                    longitude=data['longitude'],
                    altitude=data['altitude'],
                    status=data['status'],
                    last_seen=data['timestamp'],
                    capabilities=data['capabilities']
                )
                
                receivers.append(receiver)
                self.cached_peers[receiver.receiver_id] = receiver
                
            except Exception as e:
                logger.error(f"Failed to parse receiver message: {e}")
        
        # Execute query
        query.subscribe(self.client, handle_message)
        
        # Wait for messages (adjust timeout as needed)
        await asyncio.sleep(5)
        
        logger.info(f"Discovered {len(receivers)} receivers via Hedera")
        return receivers
    
    async def get_receiver_details(self, receiver_id: str) -> Optional[ReceiverInfo]:
        """Get cached receiver details"""
        return self.cached_peers.get(receiver_id)
    
    async def shutdown(self):
        """Close Hedera client"""
        if self.client:
            self.client.close()
```

### Configuration

Add to your config:

```python
config = NetworkConfig(
    hedera_network="testnet",  # or "mainnet"
    hedera_account_id="0.0.1234567",  # Your account
    hedera_private_key="302e020100300506032b6570042204...",  # Your key
    receiver_registry_topic="0.0.7654321",  # Registry topic
    max_receivers=10
)
```

## 🔧 Step 2: 4DSky Data Streaming Integration

### Install 4DSky SDK

```bash
# Install from their repository (exact command TBD based on SDK)
pip install 4dsky-sdk
```

### Implementation

Replace stub in `src/network/neuron_client.py`:

```python
from fourdskyimport (
    FourDSkyClient,
    MessageStream,
    Subscription
)

class FourDSkyDataStream(DataStreamInterface):
    """
    Real 4DSky SDK integration for Mode-S data streaming.
    """
    
    def __init__(self, config: NetworkConfig):
        self.config = config
        self.client = None
        self.subscriptions: Dict[str, Subscription] = {}
        self.callbacks: Dict[str, Callable] = {}
        
    async def initialize(self):
        """Initialize 4DSky client"""
        self.client = FourDSkyClient(
            api_key=self.config.api_key,
            endpoint=self.config.fourdskyendpoint
        )
        
        await self.client.connect()
        
    async def connect_to_receiver(self, receiver_id: str) -> bool:
        """
        Establish connection to a receiver via 4DSky.
        """
        try:
            # Request connection to specific receiver
            success = await self.client.request_connection(receiver_id)
            
            if success:
                logger.info(f"Connected to receiver {receiver_id}")
                return True
            else:
                logger.warning(f"Failed to connect to {receiver_id}")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    async def subscribe_to_stream(
        self,
        receiver_id: str,
        callback: Callable
    ) -> bool:
        """
        Subscribe to Mode-S message stream from a receiver.
        
        The callback will be called with:
        - receiver_id: str
        - timestamp: float (GPS time)
        - message: str (Mode-S hex string)
        """
        if receiver_id not in self.subscriptions:
            logger.warning(f"Not connected to {receiver_id}")
            return False
        
        try:
            # Create subscription
            sub = await self.client.subscribe(
                receiver_id=receiver_id,
                message_type="mode-s",  # or "adsb", "mlat"
                on_message=self._handle_message_wrapper(receiver_id, callback)
            )
            
            self.subscriptions[receiver_id] = sub
            self.callbacks[receiver_id] = callback
            
            logger.info(f"Subscribed to {receiver_id} Mode-S stream")
            return True
            
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            return False
    
    def _handle_message_wrapper(self, receiver_id: str, callback: Callable):
        """Wrapper to adapt 4DSky message format to our format"""
        async def handler(message):
            # Extract timestamp and message data from 4DSky format
            timestamp = message.gps_time  # GPS time in seconds
            mode_s_data = message.payload.hex()  # Hex string
            
            # Call our callback
            await callback(receiver_id, timestamp, mode_s_data)
        
        return handler
    
    async def disconnect_from_receiver(self, receiver_id: str) -> None:
        """Close connection to a receiver"""
        if receiver_id in self.subscriptions:
            sub = self.subscriptions[receiver_id]
            await sub.unsubscribe()
            
            del self.subscriptions[receiver_id]
            if receiver_id in self.callbacks:
                del self.callbacks[receiver_id]
            
            logger.info(f"Disconnected from {receiver_id}")
    
    async def shutdown(self):
        """Shutdown all connections"""
        for receiver_id in list(self.subscriptions.keys()):
            await self.disconnect_from_receiver(receiver_id)
        
        if self.client:
            await self.client.disconnect()
```

### Configuration

```python
config = NetworkConfig(
    api_key="your-4dsky-api-key",
    fourdskyendpoint="wss://api.4dsky.com/stream",  # Example
    max_receivers=10
)
```

## 🔒 Step 3: Security & Authentication

### Environment Variables

Never hardcode credentials! Use environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

config = NetworkConfig(
    hedera_network=os.getenv("HEDERA_NETWORK", "testnet"),
    hedera_account_id=os.getenv("HEDERA_ACCOUNT_ID"),
    hedera_private_key=os.getenv("HEDERA_PRIVATE_KEY"),
    receiver_registry_topic=os.getenv("RECEIVER_REGISTRY_TOPIC"),
    api_key=os.getenv("FOURDSKYAPIKEY"),
    fourdskyendpoint=os.getenv("FOURDSKYENDPOINT")
)
```

### .env File

Create `.env` file (add to .gitignore!):

```bash
# Hedera Configuration
HEDERA_NETWORK=testnet
HEDERA_ACCOUNT_ID=0.0.1234567
HEDERA_PRIVATE_KEY=302e020100300506032b657004220420...
RECEIVER_REGISTRY_TOPIC=0.0.7654321

# 4DSky Configuration
FOURDSKYAPIKEY=your-api-key-here
FOURDSKYENDPOINT=wss://api.4dsky.com/stream

# System Configuration
MAX_RECEIVERS=10
LOG_LEVEL=INFO
```

### Install dotenv

```bash
pip install python-dotenv
```

## 🚀 Step 4: Production Deployment

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY .env .env

# Set Python path
ENV PYTHONPATH=/app/src

# Run application
CMD ["python", "-m", "main"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mlat-system:
    build: .
    container_name: mlat-tracker
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8080:8080"  # If adding web API
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Run with Docker

```bash
docker-compose up -d
docker-compose logs -f
```

## 📊 Step 5: Monitoring & Logging

### Add Structured Logging

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        }
        return json.dumps(log_data)

# Setup logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### Add Metrics

```python
from dataclasses import dataclass
from typing import Dict
import time

@dataclass
class SystemMetrics:
    start_time: float
    total_signals: int = 0
    total_positions: int = 0
    errors: int = 0
    last_position_time: float = 0
    
    def get_stats(self) -> Dict:
        runtime = time.time() - self.start_time
        return {
            'runtime_seconds': runtime,
            'total_signals': self.total_signals,
            'total_positions': self.total_positions,
            'signals_per_second': self.total_signals / runtime if runtime > 0 else 0,
            'positions_per_second': self.total_positions / runtime if runtime > 0 else 0,
            'errors': self.errors
        }
```

## ✅ Testing Production Integration

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_hedera_discovery():
    """Test Hedera peer discovery"""
    config = NetworkConfig(
        hedera_network="testnet",
        hedera_account_id="0.0.12345",
        # ... other config
    )
    
    discovery = HederaPeerDiscovery(config)
    await discovery.initialize()
    
    peers = await discovery.discover_peers()
    assert len(peers) > 0
    assert all(p.status == "online" for p in peers)

@pytest.mark.asyncio
async def test_fourdskystream():
    """Test 4DSky data streaming"""
    config = NetworkConfig(api_key="test-key")
    
    stream = FourDSkyDataStream(config)
    await stream.initialize()
    
    connected = await stream.connect_to_receiver("TEST_RECV")
    assert connected == True
```

### Integration Tests

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_end_to_end_real_network():
    """Test with real Hedera and 4DSky (requires credentials)"""
    # Load real config
    config = load_production_config()
    
    # Initialize system
    client = NeuronNetworkClient(config)
    await client.initialize()
    
    # Should discover real receivers
    assert len(client.active_receivers) > 0
    
    # Should receive real data
    message_received = False
    
    async def handler(receiver_id, timestamp, message):
        nonlocal message_received
        message_received = True
    
    await client.start_streaming(handler)
    await asyncio.sleep(10)
    
    assert message_received == True
```

## 🎯 Checklist for Going Live

- [ ] Hedera account created and funded
- [ ] 4DSky SDK access obtained
- [ ] All credentials stored in environment variables
- [ ] Integration code implemented and tested
- [ ] Unit tests passing
- [ ] Integration tests passing with test credentials
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Docker deployment tested
- [ ] Error handling robust
- [ ] Documentation updated
- [ ] Performance tested under load

## 📞 Support & Resources

- **Hedera Docs**: https://docs.hedera.com/
- **Hedera Discord**: https://hedera.com/discord
- **4DSky Support**: [Contact through their platform]
- **Neuron Network**: [Community channels]

## 🚨 Troubleshooting

### Common Issues

**1. "Authentication failed" with Hedera**
- Check account ID format
- Verify private key is correct
- Ensure account has HBAR balance
- Check network (testnet vs mainnet)

**2. "No receivers discovered"**
- Verify topic ID is correct
- Check if receivers are publishing to topic
- Increase discovery timeout
- Check Hedera network status

**3. "Connection timeout" with 4DSky**
- Verify API key is valid
- Check endpoint URL
- Ensure firewall allows WebSocket connections
- Verify 4DSky service status

**4. "No signals received"**
- Check receiver is actually online
- Verify subscription was successful
- Check message filtering settings
- Monitor 4DSky connection status

---

**You're now ready to connect to the real network!** Start with testnet, validate thoroughly, then move to production. 🚀
