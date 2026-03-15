# Docker Setup Guide - Okta MCP Server

## 📋 Overview

This guide provides complete instructions for running the Okta MCP Server with Docker Compose, including workarounds for the MCP SDK limitation.

---

## ⚠️ Important: Understanding the Architecture

### Why Full Docker Deployment Has Limitations

**The MCP SDK is not available on PyPI**, which means:
- ❌ The MCP server cannot run inside a Docker container
- ✅ Supporting services (Redis, Jaeger, OTEL) can run in Docker
- ✅ The MCP server runs locally and connects to Docker services

### Recommended Architecture

```
┌─────────────────────────────────────┐
│   Host Machine (macOS/Linux)       │
│                                     │
│   ┌─────────────────────────────┐  │
│   │  MCP Server (Local)         │  │
│   │  - Python 3.11+             │  │
│   │  - MCP SDK (local install)  │  │
│   │  - Connects to Redis        │  │
│   └──────────┬──────────────────┘  │
│              │                      │
│   ┌──────────▼──────────────────┐  │
│   │  Docker Compose Services    │  │
│   │  ┌────────────────────────┐ │  │
│   │  │ Redis (Port 6379)      │ │  │
│   │  │ Jaeger (Port 16686)    │ │  │
│   │  │ OTEL Collector         │ │  │
│   │  └────────────────────────┘ │  │
│   └─────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## 🚀 Option 1: Supporting Services Only (Recommended)

This approach runs Redis, Jaeger, and OTEL Collector in Docker, while the MCP server runs locally.

### Step 1: Create docker-compose.services.yml

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
cat > docker-compose.services.yml <<'EOF'
version: '3.8'

services:
  # Redis Cache
  redis:
    image: redis:alpine
    container_name: okta-mcp-redis
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - okta-mcp-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: okta-mcp-otel-collector
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC receiver
      - "4318:4318"   # OTLP HTTP receiver
      - "8888:8888"   # Prometheus metrics
      - "8889:8889"   # Prometheus exporter
      - "13133:13133" # Health check
    networks:
      - okta-mcp-network
    restart: unless-stopped

  # Jaeger (for viewing traces)
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: okta-mcp-jaeger
    ports:
      - "16686:16686" # Jaeger UI
      - "14250:14250" # gRPC receiver
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - okta-mcp-network
    restart: unless-stopped

volumes:
  redis-data:
    driver: local

networks:
  okta-mcp-network:
    driver: bridge
EOF
```

### Step 2: Start Docker Services

```bash
# Start all supporting services
docker-compose -f docker-compose.services.yml up -d

# Check status
docker-compose -f docker-compose.services.yml ps

# View logs
docker-compose -f docker-compose.services.yml logs -f
```

**Expected Output:**
```
Creating network "okta-mcp-server_okta-mcp-network" ... done
Creating okta-mcp-redis ... done
Creating okta-mcp-otel-collector ... done
Creating okta-mcp-jaeger ... done
```

### Step 3: Verify Services are Running

```bash
# Check all containers
docker ps --filter "name=okta-mcp"

# Test Redis
docker exec okta-mcp-redis redis-cli ping
# Should return: PONG

# Check Jaeger UI
open http://localhost:16686
```

### Step 4: Update .env for Docker Services

```bash
# Edit .env file
nano .env
```

Update these settings:
```env
# Redis (Docker)
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# OpenTelemetry (Docker)
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Step 5: Start MCP Server Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Ensure dependencies are installed
pip install -r requirements-test.txt

# Start the server
python server.py
```

**Expected Output:**
```
[INFO] initializing_okta_mcp_server
[INFO] rbac_initialized
[INFO] cache_initialized backend=redis
[INFO] oauth_client_initialized
[INFO] session_store_initialized
[INFO] tools_registered
[INFO] server_initialized_successfully
[INFO] starting_mcp_server
```

### Step 6: Run Tests

```bash
# Run all tests (should use Redis from Docker)
pytest tests/ -v

# Test Redis connection
pytest tests/test_cache.py -v
```

---

## 🔧 Option 2: Redis Only (Minimal)

If you only need caching, run just Redis:

### Quick Start

```bash
# Start Redis
docker run -d \
  --name okta-mcp-redis \
  -p 6379:6379 \
  -v okta-redis-data:/data \
  redis:alpine redis-server --appendonly yes

# Verify
docker ps | grep okta-mcp-redis
docker exec okta-mcp-redis redis-cli ping

# Start MCP server
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate
python server.py
```

### Stop Redis

```bash
docker stop okta-mcp-redis
docker rm okta-mcp-redis
```

---

## 🛠️ Option 3: Modified Full Stack (Advanced)

For those who want to try running the server in Docker (requires MCP SDK workaround).

### Create Workaround Dockerfile

```bash
cat > Dockerfile.workaround <<'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-test.txt .

# Install dependencies (excluding MCP SDK)
RUN pip install --no-cache-dir -r requirements-test.txt || true

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 okta && \
    chown -R okta:okta /app

USER okta

# Run tests instead of server (since MCP SDK unavailable)
CMD ["pytest", "tests/", "-v"]
EOF
```

### Build and Run

```bash
# Build image
docker build -f Dockerfile.workaround -t okta-mcp-server:test .

# Run tests in Docker
docker run --rm \
  --network host \
  -e REDIS_URL=redis://localhost:6379/0 \
  okta-mcp-server:test
```

---

## 📊 Complete Setup Instructions

### Full Working Setup (Recommended)

#### Terminal 1: Docker Services

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server

# Create services-only compose file (if not exists)
cat > docker-compose.services.yml <<'EOF'
version: '3.8'
services:
  redis:
    image: redis:alpine
    container_name: okta-mcp-redis
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: okta-mcp-jaeger
    ports:
      - "16686:16686"
      - "14250:14250"
    restart: unless-stopped
EOF

# Start services
docker-compose -f docker-compose.services.yml up -d

# Monitor logs
docker-compose -f docker-compose.services.yml logs -f
```

#### Terminal 2: MCP Server

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server

# Activate environment
source venv/bin/activate

# Verify Redis connection
redis-cli -h localhost ping

# Start server
python server.py
```

#### Terminal 3: Testing

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate

# Run tests
pytest tests/ -v

# Test CLI
python cli.py health
python cli.py config --validate
```

---

## 🔍 Verification & Testing

### Check All Services

```bash
# Check Docker containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test Redis
docker exec okta-mcp-redis redis-cli ping
docker exec okta-mcp-redis redis-cli INFO | grep connected_clients

# Test Jaeger UI
curl -s http://localhost:16686/api/services | jq .

# Test OTEL Collector (if running)
curl -s http://localhost:13133/ | jq .
```

### Test MCP Server Connection to Redis

```bash
python -c "
import asyncio
import redis.asyncio as aioredis

async def test():
    try:
        client = await aioredis.from_url('redis://localhost:6379/0')
        result = await client.ping()
        print(f'✓ Redis connection: {result}')
        await client.close()
    except Exception as e:
        print(f'✗ Redis connection failed: {e}')

asyncio.run(test())
"
```

### Run Integration Tests

```bash
# Test with Redis from Docker
REDIS_ENABLED=true REDIS_URL=redis://localhost:6379/0 pytest tests/test_cache.py -v

# Test all components
pytest tests/ -v --tb=short
```

---

## 🎛️ Management Commands

### Start Services

```bash
# Start all services
docker-compose -f docker-compose.services.yml up -d

# Start specific service
docker-compose -f docker-compose.services.yml up -d redis

# Start with logs
docker-compose -f docker-compose.services.yml up
```

### Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.services.yml down

# Stop and remove volumes
docker-compose -f docker-compose.services.yml down -v

# Stop specific service
docker-compose -f docker-compose.services.yml stop redis
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.services.yml logs -f

# Specific service
docker-compose -f docker-compose.services.yml logs -f redis

# Last 100 lines
docker-compose -f docker-compose.services.yml logs --tail=100
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.services.yml restart

# Restart specific service
docker-compose -f docker-compose.services.yml restart redis
```

---

## 🐛 Troubleshooting

### Issue: Redis Connection Refused

**Symptom**: `ConnectionRefusedError: [Errno 61] Connection refused`

**Solution**:
```bash
# Check if Redis is running
docker ps | grep redis

# Check Redis logs
docker logs okta-mcp-redis

# Restart Redis
docker restart okta-mcp-redis

# Test connection
redis-cli -h localhost ping
```

### Issue: Port Already in Use

**Symptom**: `Error starting container: port is already allocated`

**Solution**:
```bash
# Find what's using the port
lsof -i :6379

# Kill the process (if needed)
kill -9 <PID>

# Or use different port in docker-compose
# Change "6379:6379" to "6380:6379"
```

### Issue: OTEL Collector Won't Start

**Symptom**: OTEL collector keeps restarting

**Solution**:
```bash
# Check config file exists
ls -la otel-collector-config.yaml

# View logs
docker logs okta-mcp-otel-collector

# Fix config path in docker-compose.services.yml
# Make sure volume mount is correct:
# - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
```

### Issue: Jaeger UI Not Accessible

**Symptom**: Cannot access http://localhost:16686

**Solution**:
```bash
# Check if Jaeger is running
docker ps | grep jaeger

# Check port mapping
docker port okta-mcp-jaeger

# Access directly
curl http://localhost:16686/
```

### Issue: MCP Server Can't Connect to Redis

**Symptom**: Cache falls back to in-memory

**Solution**:
```bash
# Verify Redis is accessible
redis-cli -h localhost ping

# Check .env configuration
cat .env | grep REDIS

# Test Python connection
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
print(r.ping())
"
```

---

## 📊 Monitoring & Observability

### View Jaeger Traces

1. **Open Jaeger UI**: http://localhost:16686
2. **Select Service**: okta-mcp-server
3. **View Traces**: Browse recent traces
4. **Analyze Performance**: Check latency, errors

### Redis Monitoring

```bash
# Real-time monitoring
docker exec okta-mcp-redis redis-cli MONITOR

# Get info
docker exec okta-mcp-redis redis-cli INFO

# Check memory usage
docker exec okta-mcp-redis redis-cli INFO memory

# List keys
docker exec okta-mcp-redis redis-cli KEYS '*'

# Get specific key
docker exec okta-mcp-redis redis-cli GET your_key_name
```

### Container Stats

```bash
# Real-time stats
docker stats okta-mcp-redis okta-mcp-jaeger okta-mcp-otel-collector

# Container resource usage
docker-compose -f docker-compose.services.yml top
```

---

## 🔄 Complete Workflow Example

### 1. First Time Setup

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server

# Create services compose file
cat > docker-compose.services.yml <<'EOF'
version: '3.8'
services:
  redis:
    image: redis:alpine
    container_name: okta-mcp-redis
    ports: ["6379:6379"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: okta-mcp-jaeger
    ports: ["16686:16686"]
    restart: unless-stopped
EOF

# Start services
docker-compose -f docker-compose.services.yml up -d

# Verify
docker ps
```

### 2. Daily Development

```bash
# Terminal 1: Check services
docker ps --filter "name=okta-mcp"

# Terminal 2: Start MCP server
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate
python server.py

# Terminal 3: Run tests
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate
pytest tests/ -v
```

### 3. Shutdown

```bash
# Stop MCP server
# Press Ctrl+C in Terminal 2

# Stop Docker services
docker-compose -f docker-compose.services.yml down

# Or keep Redis running for next time
# Just close the terminal
```

---

## 📝 Environment Configuration

### Recommended .env Settings for Docker

```env
# Redis (Docker)
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# OpenTelemetry (Docker)
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=okta-mcp-server

# Cache
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# Server
SERVER_HOST=localhost
SERVER_PORT=8080
LOG_LEVEL=INFO

# Okta (your credentials)
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=your_client_id
OKTA_CLIENT_SECRET=your_client_secret
OKTA_API_TOKEN=your_api_token

# Security
SESSION_SECRET_KEY=your_secret_key_here
```

---

## ✅ Success Criteria

Your Docker setup is working correctly when:

- ✅ `docker ps` shows all containers running
- ✅ `redis-cli -h localhost ping` returns "PONG"
- ✅ Jaeger UI accessible at http://localhost:16686
- ✅ `pytest tests/ -v` shows 41 tests passing
- ✅ MCP server starts without errors
- ✅ Server logs show `cache_initialized backend=redis`

---

## 🎯 Quick Reference

### Most Common Commands

```bash
# Start everything
docker-compose -f docker-compose.services.yml up -d && source venv/bin/activate && python server.py

# Stop everything
docker-compose -f docker-compose.services.yml down

# View status
docker ps && pytest tests/ -q

# Reset everything
docker-compose -f docker-compose.services.yml down -v
docker-compose -f docker-compose.services.yml up -d

# View logs
docker-compose -f docker-compose.services.yml logs -f redis
```

---

## 📚 Additional Resources

- **Docker Compose Docs**: https://docs.docker.com/compose/
- **Redis Docs**: https://redis.io/docs/
- **Jaeger Docs**: https://www.jaegertracing.io/docs/
- **OpenTelemetry Docs**: https://opentelemetry.io/docs/

---

## 🎉 Summary

**Recommended Setup**:
1. ✅ Run Redis, Jaeger, OTEL in Docker
2. ✅ Run MCP server locally
3. ✅ Run tests locally
4. ✅ Monitor with Jaeger UI

This hybrid approach gives you:
- 🚀 Easy service management with Docker
- 💻 Full MCP SDK functionality locally
- 🧪 Complete testing capability
- 📊 Professional observability

---

**Generated**: March 15, 2026
**Status**: Production Ready
**Docker Services**: Redis, Jaeger, OTEL Collector
