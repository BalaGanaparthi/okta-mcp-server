# Troubleshooting Guide - Okta MCP Server

## Common Docker Compose Errors and Solutions

---

## ❌ Error 1: OTEL Collector - Deprecated Logging Exporter

### Error Message
```
'exporters' the logging exporter has been deprecated, use the debug exporter instead
Error: failed to get config: cannot unmarshal the configuration
```

### Cause
The OpenTelemetry Collector configuration uses the old `logging` exporter which has been deprecated.

### ✅ Solution

**Option 1: Skip OTEL Collector** (Recommended)
```bash
# Start only Redis and Jaeger (skip otel-collector)
docker-compose -f docker-compose.services.yml up -d redis jaeger
```

**Option 2: Fix has been applied**
The `otel-collector-config.yaml` has been updated to use `debug` exporter instead of `logging`. Restart services:
```bash
docker-compose -f docker-compose.services.yml down
docker-compose -f docker-compose.services.yml up -d
```

**Option 3: Disable OTEL in application**
Update `.env`:
```env
OTEL_ENABLED=false
```

---

## ❌ Error 2: ModuleNotFoundError: No module named 'mcp'

### Error Message
```
Traceback (most recent call last):
  File "/app/server.py", line 11, in <module>
    from mcp.server import Server
ModuleNotFoundError: No module named 'mcp'
```

### Cause
You're trying to run the MCP server inside Docker, but the MCP SDK is not available on PyPI and cannot be installed in Docker containers.

### ✅ Solution

**The MCP server MUST run locally, not in Docker.**

1. **Stop the failing container:**
   ```bash
   docker-compose down
   # Or
   docker rm -f okta-mcp-server
   ```

2. **Use the correct docker-compose file:**
   ```bash
   # Use docker-compose.services.yml (only Redis and Jaeger)
   docker-compose -f docker-compose.services.yml up -d redis jaeger

   # NOT docker-compose.yml (includes MCP server which will fail)
   ```

3. **Run MCP server locally:**
   ```bash
   source venv/bin/activate
   python server.py
   ```

### Why This Happens
- The MCP SDK is not published on PyPI
- MCP servers are designed to run locally via stdio
- They communicate with MCP clients (like Claude Desktop) on the same machine
- Docker is used only for supporting services (Redis, Jaeger)

---

## ❌ Error 3: Orphan Containers Warning

### Error Message
```
Found orphan containers ([okta-mcp-server]) for this project.
If you removed or renamed this service in your compose file...
```

### Cause
Old containers from previous `docker-compose.yml` runs still exist.

### ✅ Solution

```bash
# Remove orphaned containers
docker-compose -f docker-compose.services.yml down --remove-orphans

# Or manually remove
docker rm -f okta-mcp-server

# Then restart services
docker-compose -f docker-compose.services.yml up -d redis jaeger
```

---

## ❌ Error 4: Port Already in Use

### Error Message
```
Error starting container: port is already allocated
Bind for 0.0.0.0:6379 failed: port is already allocated
```

### Cause
Another process (or old Docker container) is using the port.

### ✅ Solution

**For Redis (port 6379):**
```bash
# Find what's using the port
lsof -i :6379

# If it's another Redis
docker ps | grep redis
docker stop <container-name>

# Or kill the process
kill -9 <PID>

# Then restart
docker-compose -f docker-compose.services.yml up -d redis
```

**For Jaeger (port 16686):**
```bash
lsof -i :16686
docker stop <jaeger-container>
```

---

## ❌ Error 5: Permission Denied

### Error Message
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
permission denied
```

### Cause
Docker is not running or user doesn't have permissions.

### ✅ Solution

1. **Start Docker Desktop:**
   - Open Docker Desktop application
   - Wait for it to fully start
   - Check Docker icon in menu bar

2. **Verify Docker is running:**
   ```bash
   docker info
   ```

3. **Check Docker permissions (Linux):**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

---

## ❌ Error 6: Redis Connection Refused

### Error Message
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```

### Cause
Redis container is not running or not accessible.

### ✅ Solution

```bash
# Check if Redis is running
docker ps | grep redis

# If not running, start it
docker-compose -f docker-compose.services.yml up -d redis

# Test connection
docker exec okta-mcp-redis redis-cli ping

# Check Redis logs
docker logs okta-mcp-redis

# Restart if needed
docker restart okta-mcp-redis
```

---

## ❌ Error 7: Network Issues

### Error Message
```
network okta-mcp-server_okta-mcp-network not found
```

### ✅ Solution

```bash
# Recreate network
docker network create okta-mcp-server_okta-mcp-network

# Or let docker-compose create it
docker-compose -f docker-compose.services.yml up -d
```

---

## ❌ Error 8: Volume Permission Issues

### Error Message
```
mkdir: cannot create directory '/data': Permission denied
```

### ✅ Solution

```bash
# Remove old volume
docker volume rm okta-mcp-server_redis-data

# Restart with fresh volume
docker-compose -f docker-compose.services.yml up -d redis
```

---

## 🧹 Complete Cleanup and Reset

If nothing else works, do a complete cleanup:

```bash
# Stop all containers
docker-compose -f docker-compose.services.yml down

# Remove all okta-mcp containers
docker ps -a | grep okta-mcp | awk '{print $1}' | xargs docker rm -f

# Remove volumes
docker volume ls | grep okta-mcp | awk '{print $2}' | xargs docker volume rm

# Remove networks
docker network ls | grep okta-mcp | awk '{print $1}' | xargs docker network rm

# Start fresh
docker-compose -f docker-compose.services.yml up -d redis jaeger
```

---

## ✅ Verification Checklist

After fixing issues, verify everything works:

```bash
# 1. Check containers are running
docker ps | grep okta-mcp

# 2. Test Redis
docker exec okta-mcp-redis redis-cli ping
# Expected: PONG

# 3. Test Jaeger UI
curl http://localhost:16686/
# Expected: HTML response

# 4. Run tests
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate
pytest tests/test_cache.py -v
# Expected: 9 tests passing

# 5. Start MCP server locally
python server.py
# Expected: cache_initialized backend=redis
```

---

## 🎯 Best Practices

### ✅ DO:
- ✅ Use `docker-compose.services.yml` (not docker-compose.yml)
- ✅ Start only Redis and Jaeger: `up -d redis jaeger`
- ✅ Run MCP server locally: `python server.py`
- ✅ Check logs when issues occur: `docker logs <container>`
- ✅ Clean up orphaned containers: `docker ps -a`

### ❌ DON'T:
- ❌ Don't try to run MCP server in Docker
- ❌ Don't use full `docker-compose.yml` (includes MCP server)
- ❌ Don't ignore the "orphan containers" warning
- ❌ Don't skip checking if ports are available
- ❌ Don't run without verifying Docker is running

---

## 🔍 Debugging Commands

### Check What's Running
```bash
# All containers
docker ps -a

# Okta MCP containers only
docker ps -a | grep okta-mcp

# Services status
docker-compose -f docker-compose.services.yml ps
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.services.yml logs -f

# Specific service
docker logs okta-mcp-redis
docker logs okta-mcp-jaeger
docker logs okta-mcp-otel-collector

# Last 50 lines
docker logs --tail 50 okta-mcp-redis
```

### Check Resources
```bash
# Resource usage
docker stats

# Disk usage
docker system df

# Network info
docker network ls
docker network inspect okta-mcp-server_okta-mcp-network
```

### Port Verification
```bash
# Check if ports are in use
lsof -i :6379   # Redis
lsof -i :16686  # Jaeger UI
lsof -i :4317   # OTLP gRPC

# Check port mapping
docker port okta-mcp-redis
docker port okta-mcp-jaeger
```

---

## 📞 Getting Help

If you're still stuck:

1. **Check the logs:**
   ```bash
   docker-compose -f docker-compose.services.yml logs
   ```

2. **Verify Docker environment:**
   ```bash
   docker info
   docker version
   ```

3. **Check system resources:**
   ```bash
   docker system df
   ```

4. **Review configuration:**
   ```bash
   cat docker-compose.services.yml
   cat .env | grep REDIS
   ```

---

## 📚 Related Documentation

- **Quick Start**: See `DOCKER_QUICKSTART.md`
- **Complete Guide**: See `DOCKER_SETUP.md`
- **Testing**: See `TESTING_CHECKLIST.md`
- **Main Docs**: See `README.md`

---

**Last Updated**: March 15, 2026
**Status**: All known issues documented and resolved
