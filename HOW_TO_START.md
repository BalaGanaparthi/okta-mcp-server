# How to Start All Services

## 🚀 One-Command Start

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
./start-all.sh
```

This script will:
1. ✅ Check Docker is running
2. ✅ Start Redis and Jaeger containers
3. ✅ Verify services are healthy
4. ✅ Prompt you to start MCP server

---

## 📝 What Runs Where

```
Docker Services (Background):
  ✅ Redis Cache    → Port 6379
  ✅ Jaeger UI      → Port 16686

Local Python (Foreground):
  ✅ MCP Server     → stdio (connects to Redis)
```

---

## ⚡ Super Quick Start

### Terminal 1: Start Everything
```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
./start-all.sh
# Type 'y' when prompted to start MCP server
```

### Terminal 2: Run Tests (optional)
```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate
pytest tests/ -v
```

---

## 🎯 Expected Output

After running `./start-all.sh`:

```
✅ Docker is running
✅ Redis is running on port 6379
✅ Jaeger UI is running on port 16686
✅ Virtual environment found

📦 Docker Services Status
NAMES             STATUS                    PORTS
okta-mcp-redis    Up (healthy)             0.0.0.0:6379->6379/tcp
okta-mcp-jaeger   Up                       0.0.0.0:16686->16686/tcp

Do you want to start the MCP server now? (y/n)
```

If you press 'y', the MCP server will start:

```
[INFO] initializing_okta_mcp_server
[INFO] rbac_initialized
[INFO] cache_initialized backend=redis  ← Should see this!
[INFO] oauth_client_initialized
[INFO] session_store_initialized
[INFO] tools_registered
[INFO] server_initialized_successfully
[INFO] starting_mcp_server
```

---

## ✅ Verify Everything Works

```bash
# Check Docker containers
docker ps | grep okta-mcp

# Test Redis
docker exec okta-mcp-redis redis-cli ping

# Open Jaeger UI
open http://localhost:16686

# Run tests (in another terminal)
source venv/bin/activate
pytest tests/ -v
```

---

## 🛑 How to Stop

### Stop MCP Server
```bash
# Press Ctrl+C in the terminal where it's running
```

### Stop Docker Services
```bash
docker-compose -f docker-compose.services.yml down
```

---

## 🔧 Manual Start (Without Script)

If you prefer manual control:

```bash
# 1. Start Docker services
docker-compose -f docker-compose.services.yml up -d redis jaeger

# 2. Wait a moment
sleep 2

# 3. Verify Docker services
docker ps | grep okta-mcp
docker exec okta-mcp-redis redis-cli ping

# 4. Start MCP server
source venv/bin/activate
python server.py
```

---

## 🐛 Troubleshooting

### "Docker is not running"
→ Start Docker Desktop and wait for it to fully launch

### "Port is already allocated"
→ Stop conflicting services:
```bash
docker-compose -f docker-compose.services.yml down
lsof -i :6379  # Find what's using port 6379
```

### "Virtual environment not found"
→ Create it:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-test.txt
```

### MCP Server shows "cache_initialized backend=in-memory"
→ Redis isn't connected. Check `.env` file:
```bash
cat .env | grep REDIS
# Should have: REDIS_ENABLED=true
```

---

## 📚 More Information

- **Troubleshooting**: See `TROUBLESHOOTING.md`
- **Docker Details**: See `DOCKER_SETUP.md`
- **Testing**: See `TESTING_CHECKLIST.md`

---

**That's it! Run `./start-all.sh` and you're good to go!** 🎉
