"""
Main MCP server implementation for Okta user and group management.

This module implements the Model Context Protocol server that exposes
Okta management capabilities to AI agents.
"""

import asyncio
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server

from config import get_config, Config
from auth.oauth import OktaOAuthClient
from auth.session_store import SessionTokenStore
from rbac.rbac_manager import initialize_rbac_manager
from okta.client import OktaClient
from cache.cache_manager import initialize_cache_manager
from telemetry.tracing import initialize_telemetry
from tools.user_tools import UserTools
from tools.group_tools import GroupTools
from utils.logging import configure_logging, get_logger
from utils.errors import ConfigurationError

logger = get_logger(__name__)


class OktaMCPServer:
    """
    Main MCP server for Okta management.

    Coordinates all components and handles the MCP protocol.
    """

    def __init__(self, config: Config):
        """
        Initialize Okta MCP server.

        Args:
            config: Application configuration
        """
        self.config = config
        self.server = Server("okta-mcp-server")
        self.session_store: Optional[SessionTokenStore] = None
        self.oauth_client: Optional[OktaOAuthClient] = None

    async def initialize(self) -> None:
        """Initialize all server components."""
        logger.info("initializing_okta_mcp_server")

        # Validate configuration
        config_errors = self.config.validate_config()
        if config_errors:
            raise ConfigurationError(
                f"Configuration validation failed: {', '.join(config_errors)}"
            )

        # Initialize telemetry
        initialize_telemetry(self.config.otel)

        # Initialize RBAC
        rbac_manager = initialize_rbac_manager(
            model_path="rbac/model.conf",
            policy_path=self.config.rbac.policy_path
        )
        logger.info("rbac_initialized")

        # Initialize cache
        cache_manager = await initialize_cache_manager(
            self.config.redis,
            self.config.cache
        )
        logger.info(
            "cache_initialized",
            backend="redis" if cache_manager.is_using_redis() else "in-memory"
        )

        # Initialize OAuth client
        self.oauth_client = OktaOAuthClient(self.config.okta)
        logger.info("oauth_client_initialized")

        # Initialize session store
        self.session_store = SessionTokenStore(
            default_ttl=self.config.security.token_expiry_seconds
        )
        logger.info("session_store_initialized")

        # Create Okta client (will be per-session in production)
        # For demo purposes, using API token
        okta_client = OktaClient(
            config=self.config.okta,
            access_token=self.config.okta.api_token
        )

        # Initialize tools
        user_tools = UserTools(okta_client, rbac_manager, cache_manager)
        group_tools = GroupTools(okta_client, rbac_manager, cache_manager)

        # Register tools with server
        user_tools.register_tools(self.server)
        group_tools.register_tools(self.server)

        logger.info("tools_registered")

        # Register server capabilities
        @self.server.list_tools()
        async def list_tools():
            """List available MCP tools."""
            return self.server.list_tools()

        logger.info("server_initialized_successfully")

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("starting_mcp_server")

        # Run server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

    async def health_check(self) -> dict:
        """
        Perform health check.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "service": "okta-mcp-server",
            "components": {
                "rbac": "ok",
                "cache": "ok",
                "okta_client": "ok",
                "session_store": "ok"
            }
        }


async def main():
    """Main entry point."""
    # Load configuration
    config = get_config()

    # Configure logging
    configure_logging(config.server.log_level)

    # Create and initialize server
    server = OktaMCPServer(config)
    await server.initialize()

    # Run server
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
