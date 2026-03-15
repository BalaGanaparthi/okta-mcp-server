# Deployment & Testing Guide - Okta MCP Server

## 📋 Table of Contents

1. [Understanding MCP Server Deployment](#understanding-mcp-server-deployment)
2. [Local Deployment & Testing](#local-deployment--testing)
3. [Railway Deployment (Adapted)](#railway-deployment-adapted)
4. [Testing the MCP Server](#testing-the-mcp-server)
5. [Troubleshooting](#troubleshooting)

---

## Understanding MCP Server Deployment

### ⚠️ Important Note

**MCP servers are designed to run locally**, not as cloud services. They communicate via stdio (standard input/output) with MCP clients like Claude Desktop.

However, this guide provides:
- ✅ **Local deployment** (recommended for MCP)
- ✅ **Railway deployment** (adapted as an HTTP API for remote access)
- ✅ **Comprehensive testing** instructions

---

## Local Deployment & Testing

### Prerequisites

- ✅ Python 3.11+
- ✅ Git
- ✅ Okta account with admin access
- ✅ Redis (optional, will use in-memory fallback)

### Step 1: Clone and Setup

```bash
# Navigate to project
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Okta

#### 2.1: Create OAuth Application in Okta

1. **Log in to Okta Admin Console**: https://your-domain-admin.okta.com
2. **Navigate to**: Applications → Applications
3. **Click**: "Create App Integration"
4. **Select**:
   - Sign-in method: OIDC - OpenID Connect
   - Application type: Web Application
5. **Configure**:
   - App integration name: `Okta MCP Server`
   - Grant type: ✅ Authorization Code, ✅ Refresh Token
   - Sign-in redirect URIs: `http://localhost:8080/callback`
   - Sign-out redirect URIs: `http://localhost:8080`
   - Controlled access: Allow everyone in your organization
6. **Save** and note the **Client ID** and **Client Secret**

#### 2.2: Create API Token

1. **Navigate to**: Security → API → Tokens
2. **Click**: "Create Token"
3. **Name**: `MCP Server API Token`
4. **Copy** the token immediately (you won't see it again!)

#### 2.3: Create Okta Groups for RBAC

1. **Navigate to**: Directory → Groups
2. **Create these groups**:
   - `MCP-Admin` - Full access
   - `MCP-Helpdesk` - User management
   - `MCP-Auditor` - Read-only
   - `MCP-Agent` - Limited access
3. **Assign users** to appropriate groups

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
nano .env  # or use your preferred editor
```

**Required values in `.env`**:

```env
# Okta Configuration (from Step 2)
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=0oa...your_client_id
OKTA_CLIENT_SECRET=your_client_secret
OKTA_API_TOKEN=00...your_api_token
OKTA_REDIRECT_URI=http://localhost:8080/callback

# Security (generate a random key)
SESSION_SECRET_KEY=$(openssl rand -hex 32)

# Optional: Redis
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# Optional: Logging
LOG_LEVEL=INFO

# Optional: OpenTelemetry
OTEL_ENABLED=false
```

### Step 4: Validate Configuration

```bash
# Validate config
python cli.py config --validate

# Should show: "✓ Configuration is valid"
```

### Step 5: Start Redis (Optional)

```bash
# Using Docker
docker run -d --name okta-mcp-redis -p 6379:6379 redis:7-alpine

# Or using Homebrew (macOS)
brew services start redis

# Or leave disabled (will use in-memory cache)
```

### Step 6: Run the Server

```bash
# Start the MCP server
python cli.py start

# Or run directly
python server.py
```

**Expected output**:
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

### Step 7: Test Basic Functionality

In a new terminal:

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate

# Run health check
python cli.py health

# View RBAC policies
python cli.py generate-rbac

# Run tests
pytest tests/ -v
```

---

## Railway Deployment (Adapted)

⚠️ **Note**: This adapts the MCP server as an HTTP API for Railway deployment.

### Prerequisites

1. ✅ Railway account: https://railway.app
2. ✅ Railway CLI installed
3. ✅ GitHub repository pushed
4. ✅ Okta configured (same as local)

### Step 1: Install Railway CLI

```bash
# macOS/Linux
curl -fsSL https://railway.app/install.sh | sh

# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# Verify installation
railway --version
```

### Step 2: Login to Railway

```bash
railway login

# Opens browser for authentication
# Follow the prompts to authorize
```

### Step 3: Create Railway Project

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server

# Initialize Railway project
railway init

# Follow prompts:
# - Project name: okta-mcp-server
# - Environment: production
```

### Step 4: Add Redis to Railway

```bash
# Add Redis service
railway add

# Select: Redis
# This creates a Redis instance and sets REDIS_URL automatically
```

### Step 5: Configure Environment Variables

```bash
# Set Okta credentials
railway variables set OKTA_DOMAIN="your-domain.okta.com"
railway variables set OKTA_CLIENT_ID="your_client_id"
railway variables set OKTA_CLIENT_SECRET="your_client_secret"
railway variables set OKTA_API_TOKEN="your_api_token"

# Generate and set secret key
railway variables set SESSION_SECRET_KEY="$(openssl rand -hex 32)"

# Set OAuth redirect (update after deployment)
railway variables set OKTA_REDIRECT_URI="https://your-app.railway.app/callback"

# Set other configs
railway variables set LOG_LEVEL="INFO"
railway variables set REDIS_ENABLED="true"
railway variables set OTEL_ENABLED="false"
railway variables set CACHE_TTL="300"

# View all variables
railway variables
```

### Step 6: Update Okta Redirect URI

After deployment, you'll get a Railway URL like `https://okta-mcp-server-production.up.railway.app`

1. **Update Okta OAuth App**:
   - Go to your Okta OAuth app settings
   - Update Sign-in redirect URIs: `https://your-app.railway.app/callback`
   - Save

2. **Update Railway variable**:
   ```bash
   railway variables set OKTA_REDIRECT_URI="https://your-app.railway.app/callback"
   ```

### Step 7: Create railway.json Configuration

```bash
cat > railway.json <<EOF
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python server.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  },
  "healthcheck": {
    "path": "/health",
    "timeout": 30
  }
}
EOF
```

### Step 8: Deploy to Railway

```bash
# Deploy from local directory
railway up

# Or link to GitHub and deploy
railway link
railway up

# Monitor deployment
railway logs
```

### Step 9: Verify Deployment

```bash
# Get deployment URL
railway domain

# Check logs
railway logs --tail

# Check status
railway status
```

### Step 10: Set Up Custom Domain (Optional)

```bash
# Add custom domain
railway domain add your-domain.com

# Follow DNS setup instructions from Railway
```

---

## Testing the MCP Server

### Test Suite 1: Local Unit Tests

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_auth.py -v
pytest tests/test_rbac.py -v
pytest tests/test_cache.py -v
pytest tests/test_users.py -v
pytest tests/test_groups.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

**Expected Result**: ✅ 41 tests passing

### Test Suite 2: CLI Commands

```bash
# Health check
python cli.py health

# Configuration validation
python cli.py config --validate

# View configuration
python cli.py config --show

# View RBAC policies
python cli.py generate-rbac

# Check version
python cli.py version
```

### Test Suite 3: Integration with Claude Desktop

#### Step 1: Update Claude Desktop Config

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "okta": {
      "command": "python",
      "args": [
        "/Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server/server.py"
      ],
      "env": {
        "OKTA_DOMAIN": "your-domain.okta.com",
        "OKTA_CLIENT_ID": "your_client_id",
        "OKTA_CLIENT_SECRET": "your_client_secret",
        "OKTA_API_TOKEN": "your_api_token",
        "SESSION_SECRET_KEY": "your_secret_key",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

#### Step 2: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Check MCP status (should show "okta" connected)

#### Step 3: Test MCP Tools in Claude

Try these commands in Claude Desktop:

```
1. List users:
   "Use the Okta MCP server to list all users in my organization"

2. View user profile:
   "Show me the profile for user john.doe@example.com"

3. List groups:
   "List all Okta groups"

4. View group details:
   "Show me details for the Developers group"

5. Create user:
   "Create a new user: first name John, last name Smith, email john.smith@example.com"

6. Add user to group:
   "Add john.smith@example.com to the Developers group"

7. List group members:
   "Show me all members of the Developers group"
```

### Test Suite 4: Direct API Testing (Python)

Create a test script `test_mcp_direct.py`:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test MCP server directly."""

    # Configure server
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env={
            "OKTA_DOMAIN": "your-domain.okta.com",
            "OKTA_CLIENT_ID": "your_client_id",
            "OKTA_CLIENT_SECRET": "your_client_secret",
            "OKTA_API_TOKEN": "your_api_token",
            "SESSION_SECRET_KEY": "your_secret_key"
        }
    )

    # Connect to server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            print("✓ Server initialized")

            # List available tools
            tools = await session.list_tools()
            print(f"✓ Available tools: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Test list_users tool
            result = await session.call_tool(
                "list_users",
                arguments={"limit": 5}
            )
            print(f"✓ list_users result: {result}")

            # Test list_groups tool
            result = await session.call_tool(
                "list_groups",
                arguments={"limit": 5}
            )
            print(f"✓ list_groups result: {result}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
```

Run the test:

```bash
python test_mcp_direct.py
```

### Test Suite 5: RBAC Testing

Test different roles:

```python
# test_rbac_live.py
from rbac.rbac_manager import initialize_rbac_manager
from models.schemas import Role

# Initialize RBAC
rbac = initialize_rbac_manager("rbac/model.conf", "rbac/policy.csv")

# Test admin permissions
print("Testing ADMIN role:")
print(f"  create user: {rbac.check_permission(Role.ADMIN, 'user', 'create')}")
print(f"  delete group: {rbac.check_permission(Role.ADMIN, 'group', 'delete')}")

# Test helpdesk permissions
print("\nTesting HELPDESK role:")
print(f"  create user: {rbac.check_permission(Role.HELPDESK, 'user', 'create')}")
print(f"  delete group: {rbac.check_permission(Role.HELPDESK, 'group', 'delete')}")

# Test auditor permissions
print("\nTesting AUDITOR role:")
print(f"  read user: {rbac.check_permission(Role.AUDITOR, 'user', 'read')}")
print(f"  create user: {rbac.check_permission(Role.AUDITOR, 'user', 'create')}")

# Test agent permissions
print("\nTesting AGENT role:")
print(f"  read user: {rbac.check_permission(Role.AGENT, 'user', 'read')}")
print(f"  create user: {rbac.check_permission(Role.AGENT, 'user', 'create')}")
```

### Test Suite 6: Cache Testing

```bash
# Start server with Redis
docker run -d --name test-redis -p 6379:6379 redis:7-alpine

# Run cache tests
pytest tests/test_cache.py -v

# Test cache invalidation
python -c "
import asyncio
from cache.cache_manager import initialize_cache_manager
from config import RedisConfig, CacheConfig

async def test_cache():
    manager = await initialize_cache_manager(
        RedisConfig(url='redis://localhost:6379/0', enabled=True),
        CacheConfig(ttl=300, max_size=1000)
    )

    # Set value
    await manager.set('test_key', {'data': 'test_value'})
    print('✓ Cache set')

    # Get value
    value = await manager.get('test_key')
    print(f'✓ Cache get: {value}')

    # Delete value
    await manager.delete('test_key')
    print('✓ Cache delete')

    # Verify deleted
    value = await manager.get('test_key')
    print(f'✓ Verified deleted: {value is None}')

asyncio.run(test_cache())
"
```

### Test Suite 7: End-to-End Workflow

Test a complete user management workflow:

```bash
# 1. List existing users
curl -X POST http://localhost:8080/tools/list_users \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'

# 2. Create new user
curl -X POST http://localhost:8080/tools/create_user_with_password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test.user@example.com",
    "firstName": "Test",
    "lastName": "User",
    "password": "Test123!@#"
  }'

# 3. List groups
curl -X POST http://localhost:8080/tools/list_groups \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'

# 4. Add user to group
curl -X POST http://localhost:8080/tools/add_user_to_group \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "00g...",
    "user_id": "00u..."
  }'

# 5. List group members
curl -X POST http://localhost:8080/tools/list_users_in_group \
  -H "Content-Type: application/json" \
  -d '{"group_id": "00g..."}'

# 6. Remove user from group
curl -X POST http://localhost:8080/tools/remove_user_from_group \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "00g...",
    "user_id": "00u..."
  }'

# 7. Deactivate user
curl -X POST http://localhost:8080/tools/deactivate_user \
  -H "Content-Type: application/json" \
  -d '{"user_id": "00u..."}'
```

---

## Troubleshooting

### Issue: Permission Denied Errors

**Symptom**: `RBACPermissionDenied` errors

**Solution**:
```bash
# Check RBAC policies
python cli.py generate-rbac

# Verify user groups in Okta
# Ensure user is in correct Okta groups (MCP-Admin, MCP-Helpdesk, etc.)

# Test RBAC directly
python -c "
from rbac.rbac_manager import initialize_rbac_manager
from models.schemas import Role

rbac = initialize_rbac_manager('rbac/model.conf', 'rbac/policy.csv')
print(f'Admin can create user: {rbac.check_permission(Role.ADMIN, \"user\", \"create\")}')
"
```

### Issue: Okta API Errors

**Symptom**: `OktaAPIError` or authentication failures

**Solution**:
```bash
# Validate Okta credentials
python cli.py config --validate

# Test Okta connection
python -c "
import asyncio
import httpx

async def test_okta():
    client = httpx.AsyncClient()
    response = await client.get(
        'https://your-domain.okta.com/api/v1/users',
        headers={'Authorization': 'SSWS your_api_token'},
        params={'limit': 1}
    )
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    await client.aclose()

asyncio.run(test_okta())
"
```

### Issue: Redis Connection Failures

**Symptom**: Cache errors, `CacheError`

**Solution**:
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Or check if server is using in-memory fallback
tail -f server.log | grep cache_initialized
# Should show: cache_initialized backend=redis or backend=in-memory

# Disable Redis if needed
export REDIS_ENABLED=false
python server.py
```

### Issue: MCP Server Not Connecting

**Symptom**: Claude Desktop shows MCP server as disconnected

**Solution**:
```bash
# Check server logs
tail -f ~/.config/Claude/logs/mcp-server.log

# Test server directly
python server.py
# Should show initialization messages

# Validate config in Claude Desktop
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .
```

### Issue: Rate Limiting

**Symptom**: `RateLimitError` from Okta

**Solution**:
- Okta has rate limits (varies by license)
- Check Okta admin console for rate limit status
- Implement exponential backoff (already built-in)
- Consider caching more aggressively

### Issue: Session Expired

**Symptom**: Authentication errors after period of inactivity

**Solution**:
```bash
# Adjust token expiry
export TOKEN_EXPIRY_SECONDS=7200  # 2 hours

# Or re-authenticate
# The OAuth flow will automatically refresh tokens
```

---

## Performance Testing

### Load Test with Locust

Create `locustfile.py`:

```python
from locust import HttpUser, task, between

class OktaMCPUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_users(self):
        self.client.post("/tools/list_users", json={"limit": 10})

    @task(2)
    def list_groups(self):
        self.client.post("/tools/list_groups", json={"limit": 10})

    @task(1)
    def view_user(self):
        self.client.post("/tools/view_user_profile", json={"user_id": "00u..."})
```

Run load test:
```bash
pip install locust
locust -f locustfile.py --host=http://localhost:8080
```

---

## Monitoring

### View Logs

```bash
# Local
tail -f server.log

# Railway
railway logs --tail

# View structured logs
tail -f server.log | jq .
```

### Check Metrics

```bash
# Server health
python cli.py health

# Cache stats
python -c "
import asyncio
from cache.cache_manager import get_cache_manager

async def stats():
    cache = get_cache_manager()
    print(f'Using Redis: {cache.is_using_redis()}')

asyncio.run(stats())
"
```

---

## Success Criteria

Your deployment is successful when:

✅ All 41 tests pass
✅ `python cli.py health` returns healthy
✅ `python cli.py config --validate` passes
✅ Server starts without errors
✅ Claude Desktop connects to MCP server
✅ Can list users and groups
✅ Can create/modify users and groups
✅ RBAC enforcement works correctly
✅ Cache is functioning (Redis or in-memory)
✅ Logs show proper initialization

---

## Next Steps

After successful deployment:

1. **Monitor**: Set up log aggregation and alerting
2. **Scale**: Adjust Railway instance size if needed
3. **Secure**: Review and update RBAC policies
4. **Document**: Document your specific Okta group mappings
5. **Train**: Train users on MCP tool usage
6. **Iterate**: Add custom tools as needed

---

**Generated**: March 14, 2026
**Project**: Okta MCP Server
**Version**: 1.0.0
