#!/bin/bash

# Start Docker Services for Okta MCP Server
# This script starts Redis and Jaeger in Docker

set -e

echo "🚀 Starting Okta MCP Server Docker Services..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Start services
echo "📦 Starting services with Docker Compose..."
docker-compose -f docker-compose.services.yml up -d redis jaeger

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 3

# Check Redis
echo ""
echo "✓ Checking Redis..."
if docker exec okta-mcp-redis redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis is running on port 6379"
else
    echo "  ❌ Redis failed to start"
    exit 1
fi

# Check Jaeger
echo ""
echo "✓ Checking Jaeger..."
if curl -s http://localhost:16686/ > /dev/null 2>&1; then
    echo "  ✅ Jaeger UI is running on port 16686"
else
    echo "  ⚠️  Jaeger may still be starting..."
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Docker Services Started Successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Services Running:"
echo "  🗄️  Redis Cache:  localhost:6379"
echo "  📊 Jaeger UI:    http://localhost:16686"
echo ""
echo "Next Steps:"
echo "  1. Start MCP Server:"
echo "     source venv/bin/activate"
echo "     python server.py"
echo ""
echo "  2. Run Tests:"
echo "     pytest tests/ -v"
echo ""
echo "  3. View Services:"
echo "     docker-compose -f docker-compose.services.yml ps"
echo ""
echo "  4. View Logs:"
echo "     docker-compose -f docker-compose.services.yml logs -f"
echo ""
echo "  5. Stop Services:"
echo "     docker-compose -f docker-compose.services.yml down"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
