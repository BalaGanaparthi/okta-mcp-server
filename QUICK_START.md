# 🚀 Quick Start Guide

## Get Running in 5 Minutes

### 1. Set Up Environment

```bash
# Clone or navigate to directory
cd okta-mcp-server

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Okta Credentials

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required values:
```env
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=your_client_id
OKTA_CLIENT_SECRET=your_client_secret
OKTA_API_TOKEN=your_api_token
SESSION_SECRET_KEY=generate_random_key_here
```

### 3. Validate Setup

```bash
# Validate configuration
python cli.py config --validate

# Check RBAC policies
python cli.py generate-rbac

# Test health
python cli.py health
```

### 4. Start the Server

```bash
# Start MCP server
python cli.py start

# Or run directly
python server.py
```

## 🐳 Docker Quick Start

```bash
# Start everything with Docker Compose
docker-compose up --build

# Access Jaeger UI for traces
open http://localhost:16686
```

## 🧪 Run Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## 📚 What You Get

### 21 MCP Tools Ready to Use

**User Management (13 tools):**
- list_users
- view_user_profile
- create_user_with_password
- create_user_activate
- modify_user_profile
- activate_user
- deactivate_user
- suspend_user
- unsuspend_user
- unlock_user
- reset_password
- view_user_groups
- terminate_user

**Group Management (8 tools):**
- list_groups
- view_group_details
- create_group
- modify_group
- delete_group
- add_user_to_group
- remove_user_from_group
- list_users_in_group

### 4 RBAC Roles

- **Admin**: Full access to everything
- **Helpdesk**: User management + group membership
- **Auditor**: Read-only access
- **Agent**: Limited read access

### Complete Infrastructure

- ✅ OAuth 2.0 authentication
- ✅ Session management
- ✅ Redis caching (with fallback)
- ✅ OpenTelemetry tracing
- ✅ Structured logging
- ✅ RBAC enforcement
- ✅ Docker deployment
- ✅ Comprehensive tests

## 📖 Next Steps

1. **Read full documentation**: See `README.md`
2. **Explore the code**: Start with `server.py` and `tools/`
3. **Run tests**: Verify everything works
4. **Check traces**: View in Jaeger UI
5. **Integrate with Claude**: Add to your MCP client

## 🆘 Need Help?

- Configuration issues? Run `python cli.py config --validate`
- RBAC questions? Run `python cli.py generate-rbac`
- Health problems? Run `python cli.py health`
- See full docs in `README.md`

## 🎯 Project Stats

- **5,351 lines** of production Python code
- **32 Python files** with full type hints
- **42+ tests** with comprehensive coverage
- **21 MCP tools** for Okta management
- **4 RBAC roles** with hierarchical permissions
- **Enterprise-grade** architecture and security

---

**You're all set!** This is a production-ready MCP server. 🎉
