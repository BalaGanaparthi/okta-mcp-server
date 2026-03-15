# Docker Quick Start - Okta MCP Server

## 🚀 5-Minute Setup

Get Redis and Jaeger running in Docker, then start the MCP server locally.

---

## Prerequisites

- ✅ Docker Desktop running
- ✅ Python 3.11+ installed
- ✅ Virtual environment created

---

## Step 1: Start Docker Services

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server

# Option A: Use the helper script
./start-docker.sh

# Option B: Use docker-compose directly
docker-compose -f docker-compose.services.yml up -d redis jaeger
```

**Expected Output:**
```
✅ Docker Services Started Successfully!

Services Running:
  🗄️  Redis Cache:  localhost:6379
  📊 Jaeger UI:    http://localhost:16686
```

---

## Step 2: Verify Services

```bash
# Check containers
docker ps | grep okta-mcp

# Test Redis
docker exec okta-mcp-redis redis-cli ping
# Should return: PONG

# Test Jaeger UI
open http://localhost:16686
```

---

## Step 3: Start MCP Server

```bash
# Activate virtual environment
source venv/bin/activate

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

**Key indicator**: Look for `cache_initialized backend=redis` ✅

---

## Step 4: Run Tests

```bash
# In a new terminal
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Test cache specifically
pytest tests/test_cache.py -v
```

**Expected**: ✅ 41 tests passing

---

## 🎯 What's Running

```
╔════════════════════════════════════════════════════════╗
║  Component          Location            Status         ║
╠════════════════════════════════════════════════════════╣
║  Redis Cache        Docker:6379         ✅ Running     ║
║  Jaeger UI          Docker:16686        ✅ Running     ║
║  MCP Server         Local (Python)      ✅ Ready       ║
║  Tests              Local (pytest)      ✅ 41/41 Pass  ║
╚════════════════════════════════════════════════════════╝
```

---

## 📊 Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Jaeger UI** | http://localhost:16686 | View distributed traces |
| **Redis** | localhost:6379 | Caching backend |
| **MCP Server** | stdio | AI agent integration |

---

## 🛠️ Common Commands

### View Service Status
```bash
docker ps --filter "name=okta-mcp"
```

### View Logs
```bash
# Redis logs
docker logs okta-mcp-redis

# Jaeger logs
docker logs okta-mcp-jaeger

# All service logs
docker-compose -f docker-compose.services.yml logs -f
```

### Stop Services
```bash
# Stop all
docker-compose -f docker-compose.services.yml down

# Stop specific service
docker stop okta-mcp-redis
```

### Restart Services
```bash
# Restart all
docker-compose -f docker-compose.services.yml restart

# Restart Redis
docker restart okta-mcp-redis
```

---

## 🧪 Test Everything

### Quick Health Check
```bash
# Test Redis
redis-cli -h localhost ping

# Test MCP server config
python cli.py config --validate

# Test RBAC
python cli.py generate-rbac

# Run tests
pytest tests/ -q
```

### Full Test Suite
```bash
# All tests with coverage
pytest tests/ -v --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## 🐛 Troubleshooting

### Redis Not Connecting

**Problem**: Server shows `cache_initialized backend=in-memory`

**Solution**:
```bash
# Check Redis is running
docker ps | grep redis

# Test connection
docker exec okta-mcp-redis redis-cli ping

# Check environment
grep REDIS .env

# Restart Redis
docker restart okta-mcp-redis
```

### Port Already in Use

**Problem**: `port is already allocated`

**Solution**:
```bash
# Find what's using port 6379
lsof -i :6379

# Stop the conflicting service
# Then restart Docker services
docker-compose -f docker-compose.services.yml down
docker-compose -f docker-compose.services.yml up -d
```

### Docker Not Running

**Problem**: `Cannot connect to the Docker daemon`

**Solution**:
1. Start Docker Desktop
2. Wait for Docker to fully start
3. Run `docker ps` to verify
4. Retry starting services

---

## 🔄 Daily Workflow

### Morning Startup
```bash
# 1. Start Docker services
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
./start-docker.sh

# 2. Verify
docker ps | grep okta-mcp

# 3. Start MCP server
source venv/bin/activate
python server.py
```

### During Development
```bash
# Terminal 1: MCP Server running
python server.py

# Terminal 2: Run tests as you develop
pytest tests/ -v

# Terminal 3: Monitor Docker services
docker-compose -f docker-compose.services.yml logs -f
```

### End of Day
```bash
# Stop MCP server (Ctrl+C)

# Keep Docker services running (optional)
# OR stop them:
docker-compose -f docker-compose.services.yml down
```

---

## 📋 Quick Reference

### Essential Commands

```bash
# Start
./start-docker.sh

# Status
docker ps | grep okta-mcp

# Test
pytest tests/ -v

# Stop
docker-compose -f docker-compose.services.yml down

# Logs
docker-compose -f docker-compose.services.yml logs -f redis

# Restart
docker-compose -f docker-compose.services.yml restart redis
```

---

## ✅ Success Checklist

After running `./start-docker.sh`, verify:

- [x] `docker ps` shows 2 containers (redis, jaeger)
- [x] `redis-cli -h localhost ping` returns PONG
- [x] http://localhost:16686 opens Jaeger UI
- [x] `python server.py` shows `cache_initialized backend=redis`
- [x] `pytest tests/ -v` shows 41 tests passing

---

## 🎉 You're Ready!

Your Docker services are running and the MCP server is ready for:

✅ Local development and testing
✅ Integration with Claude Desktop
✅ Full caching with Redis
✅ Distributed tracing with Jaeger
✅ Production-grade setup

---

## 📚 More Information

- **Full Docker Guide**: See `DOCKER_SETUP.md`
- **Testing Guide**: See `TESTING_CHECKLIST.md`
- **Deployment Guide**: See `DEPLOYMENT_GUIDE.md`
- **Main Documentation**: See `README.md`

---

**Generated**: March 15, 2026
**Status**: Production Ready
**Services**: Redis + Jaeger in Docker, MCP Server Local
