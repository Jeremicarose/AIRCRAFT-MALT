#!/bin/bash

# MLAT System Quick Start Script - CKB Version
# This script helps you get the system running quickly with CKB blockchain

set -e  # Exit on error

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║    MLAT Aircraft Tracking System - CKB Blockchain         ║"
echo "║                    Quick Start                             ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "   Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    echo "   Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file for CKB blockchain..."
    cat > .env << EOF
# CKB Blockchain Configuration (Nervos Network)
CKB_NETWORK=testnet
CKB_RPC_URL=https://testnet.ckb.dev/rpc
CKB_INDEXER_URL=https://testnet.ckb.dev/indexer
RECEIVER_REGISTRY_TYPE_HASH=0xYOUR_TYPE_SCRIPT_HASH_HERE

# Optional: Your CKB private key (for registering receivers)
# Get from: https://faucet.nervos.org/
CKB_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE

# 4DSky Configuration (for Mode-S data streaming)
FOURDSKYAPIKEY=your_api_key_here
FOURDSKYENDPOINT=wss://api.4dsky.com/stream

# System Configuration
MAX_RECEIVERS=10
LOG_LEVEL=INFO
DATABASE_PATH=/app/data/mlat_data.db
API_KEY=change_this_secret_key
EOF
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Configure CKB blockchain settings!"
    echo ""
    echo "📚 Setup Steps:"
    echo "   1. Get CKB testnet account: https://faucet.nervos.org/"
    echo "   2. Deploy receiver registry contract (see contracts/README.md)"
    echo "   3. Update RECEIVER_REGISTRY_TYPE_HASH in .env"
    echo "   4. Add your CKB_PRIVATE_KEY"
    echo "   5. Get 4DSky API key (for data streaming)"
    echo ""
    echo "   Run: nano .env"
    echo ""
    read -p "Press Enter after you've updated .env..."
fi

# Create directories
echo "📁 Creating data directories..."
mkdir -p data logs
echo "✅ Directories created"
echo ""

# Check if CKB SDK is installed
echo "🔍 Checking Python dependencies..."
if python3 -c "import ckb" 2>/dev/null; then
    echo "✅ CKB SDK installed"
else
    echo "⚠️  CKB SDK not found"
    echo "   Installing: pip install ckb-py"
    pip install ckb-py
fi
echo ""

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose build
echo "✅ Images built"
echo ""

# Start services
echo "🚀 Starting services with CKB blockchain..."
docker-compose up -d
echo "✅ Services started"
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check health
echo "🏥 Checking service health..."
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ API is healthy"
else
    echo "⚠️  API is not responding yet. It may need more time."
fi
echo ""

# Show status
echo "📊 Service Status:"
docker-compose ps
echo ""

# Show logs
echo "📋 Recent Logs:"
echo "═══════════════════════════════════════════════════════════"
docker-compose logs --tail=20
echo "═══════════════════════════════════════════════════════════"
echo ""

# Show next steps
echo "✅ MLAT System is Running with CKB Blockchain!"
echo ""
echo "🌐 Access Points:"
echo "   Dashboard:  http://localhost:8080"
echo "   API:        http://localhost:5000/api"
echo "   Health:     http://localhost:5000/api/health"
echo ""
echo "⛓️  CKB Blockchain:"
echo "   Network:    $(grep CKB_NETWORK .env | cut -d'=' -f2)"
echo "   Explorer:   https://pudge.explorer.nervos.org/ (testnet)"
echo "   Faucet:     https://faucet.nervos.org/"
echo ""
echo "📚 Useful Commands:"
echo "   View logs:       docker-compose logs -f"
echo "   Stop system:     docker-compose down"
echo "   Restart:         docker-compose restart"
echo "   View stats:      curl http://localhost:5000/api/statistics"
echo ""
echo "📖 Documentation:"
echo "   CKB Setup:        docs/CKB_INTEGRATION_GUIDE.md"
echo "   Getting Started:  docs/GETTING_STARTED.md"
echo "   Deployment:       docs/DEPLOYMENT_GUIDE.md"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open http://localhost:8080 in your browser"
echo "   2. Read docs/CKB_INTEGRATION_GUIDE.md for blockchain setup"
echo "   3. Deploy receiver registry contract to CKB"
echo "   4. Register your receivers on CKB blockchain"
echo "   5. Monitor logs: docker-compose logs -f"
echo ""
echo "💡 Why CKB?"
echo "   ✅ Truly decentralized (no central authority)"
echo "   ✅ Permanent on-chain storage"
echo "   ✅ Censorship resistant"
echo "   ✅ Community owned"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Happy tracking with CKB blockchain! ✈️⛓️"
echo "═══════════════════════════════════════════════════════════"
echo ""