#!/bin/bash

# Start All Services for Okta MCP Server
# This script starts Docker services and MCP server

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║     Starting Okta MCP Server - All Services           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "1️⃣  Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}   ✅ Docker is running${NC}"
echo ""

# Start Docker services
echo "2️⃣  Starting Docker Services..."
echo "   Starting Redis and Jaeger..."
docker-compose -f docker-compose.services.yml up -d redis jaeger 2>&1 | grep -E "Started|Created|Running" || true
echo ""

# Wait for services to be ready
echo "3️⃣  Waiting for services to be ready..."
sleep 3

# Check Redis
echo "   Checking Redis..."
if docker exec okta-mcp-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Redis is running on port 6379${NC}"
else
    echo -e "${RED}   ❌ Redis failed to start${NC}"
    exit 1
fi

# Check Jaeger
echo "   Checking Jaeger..."
if curl -s http://localhost:16686/ > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Jaeger UI is running on port 16686${NC}"
else
    echo -e "${YELLOW}   ⚠️  Jaeger may still be starting...${NC}"
fi
echo ""

# Check virtual environment
echo "4️⃣  Checking Python environment..."
if [ ! -d "venv" ]; then
    echo -e "${RED}   ❌ Virtual environment not found${NC}"
    echo "   Run: python3 -m venv venv"
    exit 1
fi

if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}   ❌ Virtual environment not properly set up${NC}"
    exit 1
fi
echo -e "${GREEN}   ✅ Virtual environment found${NC}"
echo ""

# Show Docker services status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Docker Services Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAME|okta-mcp"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Docker Services Started Successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 Services Running:"
echo "   🗄️  Redis Cache:  localhost:6379"
echo "   📊 Jaeger UI:    http://localhost:16686"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Next: Start MCP Server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option 1: Start MCP Server (in current terminal)"
echo "  source venv/bin/activate"
echo "  python server.py"
echo ""
echo "Option 2: Start MCP Server (in background)"
echo "  source venv/bin/activate && nohup python server.py > server.log 2>&1 &"
echo "  tail -f server.log"
echo ""
echo "Option 3: Start in new terminal"
echo "  Open a new terminal and run:"
echo "  cd $(pwd)"
echo "  source venv/bin/activate"
echo "  python server.py"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Verify Everything"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "After starting MCP server, run these tests:"
echo "  pytest tests/ -v                    # All tests"
echo "  python cli.py health                # Health check"
echo "  python cli.py generate-rbac         # View RBAC"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 Stop Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Stop Docker services:"
echo "  docker-compose -f docker-compose.services.yml down"
echo ""
echo "Stop MCP server:"
echo "  Press Ctrl+C (if running in foreground)"
echo "  pkill -f 'python server.py' (if running in background)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Ask if user wants to start MCP server now
echo ""
read -p "Do you want to start the MCP server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting MCP Server..."
    echo "Press Ctrl+C to stop"
    echo ""
    source venv/bin/activate
    python server.py
fi
