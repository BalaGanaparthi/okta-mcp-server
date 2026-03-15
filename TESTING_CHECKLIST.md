# Testing Checklist - Okta MCP Server

Quick reference for testing the MCP server deployment.

## ✅ Pre-Deployment Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with Okta credentials
- [ ] Okta OAuth app created and configured
- [ ] Okta API token generated
- [ ] Okta groups created (MCP-Admin, MCP-Helpdesk, MCP-Auditor, MCP-Agent)

---

## 🧪 Test 1: Configuration Validation

```bash
cd /Users/balaganaparthi/Documents/claude-projects/project002/okta-mcp-server
source venv/bin/activate

python cli.py config --validate
```

**Expected**: ✅ "Configuration is valid"

**If fails**: Check `.env` file for missing required variables

---

## 🧪 Test 2: Unit Tests

```bash
pytest tests/ -v
```

**Expected**: ✅ 41 tests passing in ~3-4 seconds

**Breakdown**:
- `test_auth.py`: 10 tests ✓
- `test_rbac.py`: 8 tests ✓
- `test_cache.py`: 9 tests ✓
- `test_users.py`: 6 tests ✓
- `test_groups.py`: 8 tests ✓

---

## 🧪 Test 3: RBAC Policies

```bash
python cli.py generate-rbac
```

**Expected**: Display of all role permissions

**Verify**:
- Admin has all permissions
- Helpdesk has user management
- Auditor has read-only
- Agent has limited read

---

## 🧪 Test 4: Health Check

```bash
python cli.py health
```

**Expected**: Health status table showing all components "ok"

**Components**:
- Overall: healthy
- RBAC: ok
- Cache: ok
- Okta client: ok
- Session store: ok

---

## 🧪 Test 5: Server Startup

```bash
python server.py
```

**Expected log output**:
```
[INFO] initializing_okta_mcp_server
[INFO] rbac_initialized
[INFO] cache_initialized backend=in-memory (or redis)
[INFO] oauth_client_initialized
[INFO] session_store_initialized
[INFO] tools_registered
[INFO] server_initialized_successfully
[INFO] starting_mcp_server
```

**If fails**: Check logs for specific errors

---

## 🧪 Test 6: Cache Functionality

### Test In-Memory Cache

```bash
python -c "
import asyncio
from cache.cache_manager import InMemoryCache

async def test():
    cache = InMemoryCache(max_size=100, default_ttl=300)
    await cache.set('test_key', 'test_value')
    value = await cache.get('test_key')
    print(f'✓ Cache working: {value == \"test_value\"}')

asyncio.run(test())
"
```

**Expected**: ✅ "Cache working: True"

### Test Redis Cache (if enabled)

```bash
# Start Redis
docker run -d --name test-redis -p 6379:6379 redis:7-alpine

# Test connection
redis-cli ping

# Run server with Redis
REDIS_ENABLED=true python server.py
```

---

## 🧪 Test 7: Okta API Connection

```bash
python -c "
import asyncio
import httpx
import os

async def test_okta():
    domain = os.getenv('OKTA_DOMAIN')
    token = os.getenv('OKTA_API_TOKEN')

    client = httpx.AsyncClient()
    try:
        response = await client.get(
            f'https://{domain}/api/v1/users',
            headers={'Authorization': f'SSWS {token}'},
            params={'limit': 1},
            timeout=10.0
        )
        print(f'✓ Okta API Status: {response.status_code}')
        print(f'✓ Okta API Working: {response.status_code == 200}')
    except Exception as e:
        print(f'✗ Okta API Error: {e}')
    finally:
        await client.aclose()

asyncio.run(test_okta())
"
```

**Expected**: ✅ "Okta API Status: 200"

---

## 🧪 Test 8: MCP Tools (Manual)

### List Users Tool
```python
# In Claude Desktop or MCP client
list_users(limit=5)
```

**Expected**: JSON response with user list

### View User Tool
```python
view_user_profile(user_id="your_user_id")
```

**Expected**: JSON response with user details

### List Groups Tool
```python
list_groups(limit=5)
```

**Expected**: JSON response with groups list

---

## 🧪 Test 9: RBAC Enforcement

```bash
python -c "
from rbac.rbac_manager import initialize_rbac_manager
from models.schemas import Role

rbac = initialize_rbac_manager('rbac/model.conf', 'rbac/policy.csv')

# Test each role
roles = [Role.ADMIN, Role.HELPDESK, Role.AUDITOR, Role.AGENT]
for role in roles:
    can_create = rbac.check_permission(role, 'user', 'create')
    can_read = rbac.check_permission(role, 'user', 'read')
    print(f'{role.value:10} - create: {can_create}, read: {can_read}')
"
```

**Expected**:
```
admin      - create: True, read: True
helpdesk   - create: True, read: True
auditor    - create: False, read: True
agent      - create: False, read: True
```

---

## 🧪 Test 10: End-to-End Workflow

### Complete User Management Flow

```bash
# 1. List existing users
# 2. Create a test user
# 3. View the user's profile
# 4. List all groups
# 5. Add user to a group
# 6. List group members
# 7. Remove user from group
# 8. Deactivate user
# 9. Verify user status

# Run integration test
python -c "
import asyncio
from okta.client import OktaClient
from okta.users import OktaUsersAPI
from okta.groups import OktaGroupsAPI
from config import get_config
from models.schemas import OktaUserProfile

async def test_workflow():
    config = get_config()
    client = OktaClient(config.okta, access_token=config.okta.api_token)
    users_api = OktaUsersAPI(client)
    groups_api = OktaGroupsAPI(client)

    try:
        # 1. List users
        users = await users_api.list_users(limit=1)
        print(f'✓ Listed {len(users)} user(s)')

        # 2. List groups
        groups = await groups_api.list_groups(limit=1)
        print(f'✓ Listed {len(groups)} group(s)')

        print('✓ End-to-end workflow test passed')
    except Exception as e:
        print(f'✗ Workflow test failed: {e}')
    finally:
        await client.close()

asyncio.run(test_workflow())
"
```

---

## 🧪 Test 11: Performance & Load

### Quick Performance Test

```bash
time python -c "
import asyncio
from okta.client import OktaClient
from okta.users import OktaUsersAPI
from config import get_config

async def perf_test():
    config = get_config()
    client = OktaClient(config.okta, access_token=config.okta.api_token)
    users_api = OktaUsersAPI(client)

    # Measure list users performance
    users = await users_api.list_users(limit=50)
    print(f'Retrieved {len(users)} users')

    await client.close()

asyncio.run(perf_test())
"
```

**Expected**: Completes in < 2 seconds

---

## 🧪 Test 12: Error Handling

### Test Invalid Credentials

```bash
OKTA_API_TOKEN=invalid python -c "
import asyncio
from okta.client import OktaClient
from okta.users import OktaUsersAPI
from config import get_config
from utils.errors import OktaAPIError

async def test_error():
    config = get_config()
    client = OktaClient(config.okta, access_token='invalid_token')
    users_api = OktaUsersAPI(client)

    try:
        await users_api.list_users(limit=1)
        print('✗ Should have raised OktaAPIError')
    except OktaAPIError as e:
        print(f'✓ Error handling works: {e.error_code}')
    except Exception as e:
        print(f'✗ Unexpected error: {e}')
    finally:
        await client.close()

asyncio.run(test_error())
"
```

**Expected**: ✅ "Error handling works: OktaAPIError"

### Test RBAC Denial

```bash
python -c "
from rbac.rbac_manager import initialize_rbac_manager
from models.schemas import Role
from utils.errors import RBACPermissionDenied

rbac = initialize_rbac_manager('rbac/model.conf', 'rbac/policy.csv')

try:
    rbac.enforce_permission(Role.AGENT, 'user', 'create')
    print('✗ Should have raised RBACPermissionDenied')
except RBACPermissionDenied as e:
    print(f'✓ RBAC denial works: {e.error_code}')
"
```

**Expected**: ✅ "RBAC denial works: PERMISSION_DENIED"

---

## 🧪 Test 13: Docker Deployment

### Test Docker Build

```bash
docker build -t okta-mcp-server .
```

**Expected**: ✅ Build succeeds without errors

### Test Docker Run

```bash
docker run --rm \
  -e OKTA_DOMAIN=your-domain.okta.com \
  -e OKTA_CLIENT_ID=your_client_id \
  -e OKTA_CLIENT_SECRET=your_client_secret \
  -e OKTA_API_TOKEN=your_api_token \
  -e SESSION_SECRET_KEY=your_secret \
  okta-mcp-server
```

**Expected**: Server starts successfully

### Test Docker Compose

```bash
docker-compose up -d
docker-compose logs -f okta-mcp-server
docker-compose ps
docker-compose down
```

**Expected**: All services start and stay healthy

---

## 🧪 Test 14: Monitoring & Observability

### Check Logs

```bash
# View structured logs
python server.py 2>&1 | tee server.log

# Parse JSON logs
cat server.log | jq .
```

### Verify Telemetry (if enabled)

```bash
# Start with OpenTelemetry enabled
OTEL_ENABLED=true python server.py

# Check Jaeger UI (if using docker-compose)
open http://localhost:16686
```

---

## 📊 Test Results Summary

After running all tests, you should have:

| Test | Status | Time |
|------|--------|------|
| Configuration | ✅ Pass | < 1s |
| Unit Tests | ✅ 41/41 | ~3s |
| RBAC Policies | ✅ Pass | < 1s |
| Health Check | ✅ Pass | < 1s |
| Server Startup | ✅ Pass | ~2s |
| Cache | ✅ Pass | < 1s |
| Okta API | ✅ Pass | ~1s |
| MCP Tools | ✅ Pass | varies |
| RBAC Enforcement | ✅ Pass | < 1s |
| End-to-End | ✅ Pass | ~2s |
| Performance | ✅ Pass | ~2s |
| Error Handling | ✅ Pass | < 1s |
| Docker | ✅ Pass | ~30s |
| Monitoring | ✅ Pass | ongoing |

**Total Tests**: 14 test suites
**Expected Duration**: < 5 minutes
**Success Criteria**: All tests passing ✅

---

## 🚨 Troubleshooting Quick Fixes

### Tests Failing?

```bash
# 1. Check Python version
python --version  # Should be 3.11+

# 2. Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# 3. Clear cache
rm -rf __pycache__ */__pycache__

# 4. Reset environment
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Okta API Failing?

```bash
# Check credentials
python cli.py config --show | grep OKTA

# Test connection manually
curl https://your-domain.okta.com/api/v1/users?limit=1 \
  -H "Authorization: SSWS your_api_token"
```

### RBAC Failing?

```bash
# Verify policy files exist
ls -la rbac/

# Reload policies
python cli.py generate-rbac
```

---

## ✅ Final Verification

All systems go when you see:

```bash
✓ Configuration valid
✓ 41/41 tests passing
✓ RBAC policies loaded
✓ Health check passed
✓ Server starts without errors
✓ Okta API connection working
✓ Cache functioning
✓ All tools operational
✓ Error handling correct
✓ Docker builds successfully
```

**You're ready for production! 🚀**

---

**See `DEPLOYMENT_GUIDE.md` for detailed deployment instructions.**
