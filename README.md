# Okta MCP Server

A production-grade Model Context Protocol (MCP) server that enables AI agents to securely manage Okta users and groups through the Okta Management API.

## Features

- **🔐 Secure Authentication**: OAuth 2.0 Authorization Code Flow with Okta
- **👥 User Management**: Complete CRUD operations for Okta users
- **🏢 Group Management**: Full group administration capabilities
- **🛡️ RBAC**: Role-based access control using Casbin
- **💾 Caching**: Redis-backed caching with in-memory fallback
- **📊 Observability**: OpenTelemetry distributed tracing and structured logging
- **🐳 Containerized**: Docker and Docker Compose support
- **🧪 Well-Tested**: Comprehensive unit and integration tests
- **⚡ Production-Ready**: Async operations, retry logic, rate limiting

## Architecture

```
┌─────────────────┐
│   AI Agent      │
│   (MCP Client)  │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────────────────────────────────┐
│         Okta MCP Server                     │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Tools   │  │   RBAC   │  │  Cache   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │              │        │
│  ┌────▼─────────────▼──────────────▼─────┐ │
│  │        Okta Client (Async HTTP)       │ │
│  └────────────────┬──────────────────────┘ │
└───────────────────┼────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │   Okta Management   │
         │        API          │
         └─────────────────────┘
```

## Technology Stack

- **Language**: Python 3.11+
- **MCP SDK**: Official MCP Python SDK
- **HTTP Client**: httpx (async)
- **Configuration**: pydantic, python-dotenv
- **Caching**: Redis with aioredis
- **RBAC**: Casbin
- **Observability**: OpenTelemetry, structlog
- **CLI**: Typer with Rich
- **Testing**: pytest, pytest-asyncio, respx
- **Containerization**: Docker, Docker Compose

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- Okta account with admin access
- Redis (optional, will use in-memory cache if unavailable)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/okta-mcp-server.git
cd okta-mcp-server
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Okta credentials
```

### Configuration

#### Okta Setup

1. **Create OAuth Application** in Okta:
   - Go to Applications → Create App Integration
   - Choose "OIDC - OpenID Connect"
   - Choose "Web Application"
   - Configure redirect URI: `http://localhost:8080/callback`
   - Note the Client ID and Client Secret

2. **Create API Token** (optional, for service-to-service):
   - Go to Security → API
   - Click "Create Token"
   - Save the token securely

3. **Configure Group Mappings** for RBAC:
   - Create Okta groups: `MCP-Admin`, `MCP-Helpdesk`, `MCP-Auditor`, `MCP-Agent`
   - Assign users to appropriate groups

#### Environment Variables

Required variables in `.env`:

```env
# Okta Configuration
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=your_client_id
OKTA_CLIENT_SECRET=your_client_secret
OKTA_REDIRECT_URI=http://localhost:8080/callback
OKTA_API_TOKEN=your_api_token

# Security
SESSION_SECRET_KEY=generate_strong_random_key
```

Optional variables:

```env
# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# Cache
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# Server
SERVER_HOST=localhost
SERVER_PORT=8080
LOG_LEVEL=INFO

# OpenTelemetry
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Running Locally

#### Start the Server

```bash
# Using CLI
python cli.py start

# Or directly
python server.py
```

#### Validate Configuration

```bash
python cli.py config --validate
```

#### Check Health

```bash
python cli.py health
```

#### View RBAC Policies

```bash
python cli.py generate-rbac
```

### Running with Docker

#### Build and Start All Services

```bash
docker-compose up --build
```

This starts:
- Okta MCP Server
- Redis (cache)
- OpenTelemetry Collector
- Jaeger (trace viewer)

#### Access Services

- **MCP Server**: stdio interface
- **Jaeger UI**: http://localhost:16686
- **Prometheus Metrics**: http://localhost:8889

#### Stop Services

```bash
docker-compose down
```

## RBAC Roles and Permissions

The server implements four roles with hierarchical permissions:

### Admin
Full access to all operations:
- Users: create, read, update, delete, suspend, activate, unlock, reset_password, terminate
- Groups: create, read, update, delete, add_member, remove_member

### Helpdesk
User management focused:
- Users: create, read, update, suspend, unsuspend, activate, unlock, reset_password
- Groups: read, add_member, remove_member

### Auditor
Read-only access:
- Users: read
- Groups: read

### Agent
Limited read access:
- Users: read
- Groups: read

Roles inherit permissions hierarchically: Admin → Helpdesk → Auditor → Agent

## MCP Tools

### User Tools

| Tool | Description | Required Role |
|------|-------------|---------------|
| `list_users` | List users with optional filtering | Agent+ |
| `view_user_profile` | View detailed user profile | Agent+ |
| `create_user_with_password` | Create new user with password | Helpdesk+ |
| `create_user_activate` | Create and activate user | Helpdesk+ |
| `modify_user_profile` | Update user profile | Helpdesk+ |
| `activate_user` | Activate user account | Helpdesk+ |
| `deactivate_user` | Deactivate user account | Admin |
| `suspend_user` | Suspend user account | Helpdesk+ |
| `unsuspend_user` | Unsuspend user account | Helpdesk+ |
| `unlock_user` | Unlock locked account | Helpdesk+ |
| `reset_password` | Reset user password | Helpdesk+ |
| `view_user_groups` | View user's group memberships | Agent+ |
| `terminate_user` | Permanently delete user | Admin |

### Group Tools

| Tool | Description | Required Role |
|------|-------------|---------------|
| `list_groups` | List all groups | Agent+ |
| `view_group_details` | View group details | Agent+ |
| `create_group` | Create new group | Admin |
| `modify_group` | Update group properties | Admin |
| `delete_group` | Delete group | Admin |
| `add_user_to_group` | Add user to group | Helpdesk+ |
| `remove_user_from_group` | Remove user from group | Helpdesk+ |
| `list_users_in_group` | List group members | Agent+ |

## Using the MCP Server

### From Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "okta": {
      "command": "python",
      "args": ["/path/to/okta-mcp-server/server.py"],
      "env": {
        "OKTA_DOMAIN": "your-domain.okta.com",
        "OKTA_CLIENT_ID": "your_client_id",
        "OKTA_CLIENT_SECRET": "your_client_secret",
        "OKTA_API_TOKEN": "your_api_token"
      }
    }
  }
}
```

### From Python

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Create client
server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
    env={"OKTA_DOMAIN": "your-domain.okta.com", ...}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # List available tools
        tools = await session.list_tools()

        # Call a tool
        result = await session.call_tool(
            "list_users",
            arguments={"limit": 10}
        )
```

## Development

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_users.py

# Verbose output
pytest -v
```

### Code Quality

```bash
# Type checking
mypy .

# Linting
ruff check .

# Format code
black .
```

### Project Structure

```
okta-mcp-server/
├── server.py              # Main MCP server
├── cli.py                 # CLI interface
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Multi-container setup
│
├── auth/                 # Authentication
│   ├── oauth.py         # OAuth flow implementation
│   └── session_store.py # Session management
│
├── rbac/                # RBAC implementation
│   ├── policy.csv      # Casbin policies
│   ├── model.conf      # Casbin model
│   └── rbac_manager.py # RBAC enforcement
│
├── okta/               # Okta API integration
│   ├── client.py      # Async HTTP client
│   ├── users.py       # User operations
│   └── groups.py      # Group operations
│
├── tools/             # MCP tool implementations
│   ├── user_tools.py # User management tools
│   └── group_tools.py# Group management tools
│
├── cache/            # Caching layer
│   └── cache_manager.py
│
├── telemetry/       # Observability
│   └── tracing.py   # OpenTelemetry setup
│
├── models/          # Data models
│   └── schemas.py
│
├── utils/          # Utilities
│   ├── logging.py # Structured logging
│   └── errors.py  # Custom exceptions
│
└── tests/         # Test suite
    ├── conftest.py
    ├── test_auth.py
    ├── test_rbac.py
    ├── test_cache.py
    ├── test_users.py
    └── test_groups.py
```

## Observability

### Structured Logging

Logs are output in structured JSON format (production) or colored console format (development):

```json
{
  "event": "okta_api_request",
  "level": "info",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "app": "okta-mcp-server",
  "method": "GET",
  "endpoint": "/users",
  "session_id": "abc123"
}
```

### Distributed Tracing

View traces in Jaeger UI (http://localhost:16686) when running with Docker Compose.

Trace spans include:
- MCP tool executions
- Okta API calls
- Cache operations
- Authentication flow

## Security Considerations

### Best Practices

1. **Never commit secrets**: Use environment variables or secret management
2. **Rotate credentials**: Regularly rotate OAuth secrets and API tokens
3. **Least privilege**: Assign minimal required RBAC roles
4. **Audit logging**: Monitor all user and group modifications
5. **Rate limiting**: Respect Okta rate limits (handled automatically)
6. **Token expiry**: Sessions expire based on TOKEN_EXPIRY_SECONDS
7. **Input validation**: All inputs are validated using Pydantic

### Production Deployment

For production use:

1. Use secrets management (e.g., AWS Secrets Manager, HashiCorp Vault)
2. Enable Redis for distributed caching
3. Configure log aggregation (e.g., ELK, Splunk)
4. Set up monitoring and alerting
5. Use TLS for all connections
6. Implement IP allowlisting
7. Regular security audits

## Troubleshooting

### Common Issues

**"RBAC manager not initialized"**
- Ensure `rbac/policy.csv` and `rbac/model.conf` exist
- Check RBAC_POLICY_PATH in configuration

**"Redis connection failed"**
- Verify Redis is running: `redis-cli ping`
- Check REDIS_URL configuration
- Server will fall back to in-memory cache

**"Authentication failed"**
- Verify Okta credentials in .env
- Check Okta domain format (no https://)
- Ensure OAuth application is configured correctly

**"Permission denied"**
- Check user's RBAC role assignment
- Verify Casbin policies are loaded
- Review logs for permission checks

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python server.py
```

## Performance

### Benchmarks

- User listing (cached): ~5ms
- User listing (uncached): ~200ms
- User creation: ~500ms
- Group operations: ~100-300ms

### Optimization Tips

1. Use Redis for distributed caching
2. Adjust CACHE_TTL based on your needs
3. Enable connection pooling in production
4. Monitor rate limits via telemetry

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Follow PEP 8 style guide
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: https://github.com/your-org/okta-mcp-server/issues
- **Discussions**: https://github.com/your-org/okta-mcp-server/discussions
- **Email**: support@yourcompany.com

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Okta Management API](https://developer.okta.com/docs/reference/core-okta-api/)
- [Casbin](https://casbin.org/)
- [OpenTelemetry](https://opentelemetry.io/)

---

Built with ❤️ for the AI agent ecosystem
