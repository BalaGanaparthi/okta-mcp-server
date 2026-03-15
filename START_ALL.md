# How to Start All Services - Okta MCP Server

## 🚀 Quick Start (One Command)

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
./start-all.sh
```

This will start:
1. ✅ Docker services (Redis + Jaeger)
2. ✅ MCP Server (local Python)
3. ✅ Verify everything is working

---

## 📋 Manual Step-by-Step

If you prefer to start services manually:

### Step 1: Start Docker Services

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server

# Start Redis and Jaeger
docker-compose -f docker-compose.services.yml up -d redis jaeger
```

**Expected Output**:
```
✅ Container okta-mcp-redis Started
✅ Container okta-mcp-jaeger Started
```

### Step 2: Verify Docker Services

```bash
# Check status
docker ps | grep okta-mcp

# Test Redis
docker exec okta-mcp-redis redis-cli ping
# Should return: PONG

# Test Jaeger UI
curl -s http://localhost:16686/ | head -c 50
# Should return: HTML content
```

### Step 3: Start MCP Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python server.py
```

**Expected Output**:
```
[INFO] initializing_okta_mcp_server
[INFO] rbac_initialized
[INFO] cache_initialized backend=redis  ← Important!
[INFO] oauth_client_initialized
[INFO] session_store_initialized
[INFO] tools_registered
[INFO] server_initialized_successfully
[INFO] starting_mcp_server
```

---

## 🎯 What Gets Started

```
╔═══════════════════════════════════════════════════════╗
║  Component         Location        Port      Status  ║
╠═══════════════════════════════════════════════════════╣
║  Redis Cache       Docker          6379      Running ║
║  Jaeger UI         Docker          16686     Running ║
║  MCP Server        Local (Python)  stdio     Running ║
╚═══════════════════════════════════════════════════════╝
```

---

## 🧪 Verify Everything is Working

After starting all services, run these checks:

```bash
# Check Docker services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep okta-mcp

# Test Redis connection
redis-cli -h localhost ping

# Test cache with Redis
pytest tests/test_cache.py -v

# Run all tests
pytest tests/ -q

# Check health
python cli.py health
```

**Expected Results**:
- ✅ 2 Docker containers running
- ✅ Redis responds with PONG
- ✅ 41 tests passing
- ✅ Health check shows "ok"

---

## 🛑 How to Stop All Services

### Stop MCP Server
```bash
# Press Ctrl+C in the terminal where server.py is running
```

### Stop Docker Services
```bash
docker-compose -f docker-compose.services.yml down
```

### Complete Shutdown
```bash
# Stop everything
docker-compose -f docker-compose.services.yml down

# Or keep Docker services running for next time
# (they restart automatically on system reboot)
```

---

## 🔄 Restart Services

### Restart Docker Services
```bash
docker-compose -f docker-compose.services.yml restart
```

### Restart MCP Server
```bash
# Stop with Ctrl+C, then:
source venv/bin/activate
python server.py
```

---

## 📊 Check Service Status

### Docker Services
```bash
# View running containers
docker ps | grep okta-mcp

# View logs
docker-compose -f docker-compose.services.yml logs -f

# Check health
docker-compose -f docker-compose.services.yml ps
```

### MCP Server
```bash
# Server is running if you see this in terminal:
# [INFO] starting_mcp_server

# Test with CLI
python cli.py health
python cli.py config --validate
```

---

## 🎨 Multiple Terminal Setup

For development, use 3 terminals:

### Terminal 1: Docker Services
```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
docker-compose -f docker-compose.services.yml up
# Keep this running to see logs
```

### Terminal 2: MCP Server
```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate
python server.py
# Keep this running
```

### Terminal 3: Testing/Development
```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate

# Run tests
pytest tests/ -v

# Try CLI commands
python cli.py health
python cli.py generate-rbac

# Test individual components
pytest tests/test_cache.py -v
```

---

## ⚡ Quick Commands Reference

```bash
# Start everything
./start-all.sh

# Start Docker only
docker-compose -f docker-compose.services.yml up -d redis jaeger

# Start MCP server only
source venv/bin/activate && python server.py

# Stop Docker
docker-compose -f docker-compose.services.yml down

# View all logs
docker-compose -f docker-compose.services.yml logs -f

# Check everything
docker ps && pytest tests/ -q
```

---

## 🐛 Troubleshooting

### Services Won't Start

**Check Docker is running**:
```bash
docker info
```

**Check ports are available**:
```bash
lsof -i :6379  # Redis
lsof -i :16686 # Jaeger
```

**Clean up old containers**:
```bash
docker-compose -f docker-compose.services.yml down --remove-orphans
```

### MCP Server Won't Start

**Check virtual environment**:
```bash
source venv/bin/activate
which python
# Should show: .../venv/bin/python
```

**Check dependencies**:
```bash
pip install -r requirements-test.txt
```

**Check configuration**:
```bash
python cli.py config --validate
```

### Redis Connection Issues

**Verify Redis is running**:
```bash
docker ps | grep redis
docker exec okta-mcp-redis redis-cli ping
```

**Check .env configuration**:
```bash
grep REDIS .env
# Should have:
# REDIS_URL=redis://localhost:6379/0
# REDIS_ENABLED=true
```

---

## ✅ Success Checklist

After starting services, verify:

- [ ] Docker Desktop is running
- [ ] `docker ps` shows 2 containers (redis, jaeger)
- [ ] `redis-cli -h localhost ping` returns PONG
- [ ] http://localhost:16686 opens Jaeger UI
- [ ] `python server.py` starts without errors
- [ ] Server logs show `cache_initialized backend=redis`
- [ ] `pytest tests/ -q` shows 41 tests passing

---

## 📖 Next Steps

Once all services are running:

1. **Run Tests**: `pytest tests/ -v`
2. **View Jaeger UI**: Open http://localhost:16686
3. **Check Health**: `python cli.py health`
4. **View RBAC**: `python cli.py generate-rbac`
5. **Integrate with Claude Desktop**: See README.md

---

## 📚 Related Documentation

- **Troubleshooting**: `TROUBLESHOOTING.md`
- **Docker Setup**: `DOCKER_SETUP.md`
- **Quick Start**: `DOCKER_QUICKSTART.md`
- **Testing**: `TESTING_CHECKLIST.md`
- **Main Docs**: `README.md`

---

**Last Updated**: March 15, 2026
**Status**: All Services Working
