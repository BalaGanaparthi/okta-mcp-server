"""
MCP tools for Okta user management.

This module defines all MCP tools for managing users in Okta.
"""

from typing import Optional, Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent

from okta.client import OktaClient
from okta.users import OktaUsersAPI
from models.schemas import (
    OktaUserProfile,
    ToolResponse,
    Role
)
from rbac.rbac_manager import RBACManager
from cache.cache_manager import CacheManager
from telemetry.tracing import trace_mcp_tool
from utils.logging import get_logger
from utils.errors import OktaMCPError

logger = get_logger(__name__)


class UserTools:
    """Collection of MCP tools for user management."""

    def __init__(
        self,
        okta_client: OktaClient,
        rbac_manager: RBACManager,
        cache_manager: CacheManager
    ):
        """
        Initialize user tools.

        Args:
            okta_client: Okta API client
            rbac_manager: RBAC manager
            cache_manager: Cache manager
        """
        self.okta_client = okta_client
        self.users_api = OktaUsersAPI(okta_client)
        self.rbac = rbac_manager
        self.cache = cache_manager

    def register_tools(self, server: Server) -> None:
        """
        Register all user tools with MCP server.

        Args:
            server: MCP server instance
        """
        tools = [
            Tool(
                name="list_users",
                description="List Okta users with optional filtering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "filter": {"type": "string", "description": "Filter expression"},
                        "limit": {"type": "integer", "description": "Maximum results"}
                    }
                }
            ),
            Tool(
                name="view_user_profile",
                description="View detailed user profile information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID or email"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="create_user_with_password",
                description="Create a new user with password",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "description": "User email"},
                        "firstName": {"type": "string", "description": "First name"},
                        "lastName": {"type": "string", "description": "Last name"},
                        "password": {"type": "string", "description": "Password"},
                        "activate": {"type": "boolean", "description": "Activate immediately"}
                    },
                    "required": ["email", "firstName", "lastName", "password"]
                }
            ),
            Tool(
                name="create_user_activate",
                description="Create and activate a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "firstName": {"type": "string"},
                        "lastName": {"type": "string"}
                    },
                    "required": ["email", "firstName", "lastName"]
                }
            ),
            Tool(
                name="modify_user_profile",
                description="Modify user profile fields",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "updates": {"type": "object", "description": "Profile fields to update"}
                    },
                    "required": ["user_id", "updates"]
                }
            ),
            Tool(
                name="activate_user",
                description="Activate a user account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "send_email": {"type": "boolean"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="deactivate_user",
                description="Deactivate a user account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="suspend_user",
                description="Suspend a user account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="unsuspend_user",
                description="Unsuspend a user account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="unlock_user",
                description="Unlock a locked user account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="reset_password",
                description="Reset user password",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "send_email": {"type": "boolean"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="view_user_groups",
                description="View groups a user belongs to",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="terminate_user",
                description="Permanently delete a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"}
                    },
                    "required": ["user_id"]
                }
            )
        ]

        # Register all tools
        for tool in tools:
            @server.call_tool()
            @trace_mcp_tool(tool.name)
            async def handler(name: str, arguments: dict, role: Role = Role.AGENT):
                return await self.handle_tool_call(name, arguments, role)

    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        role: Role
    ) -> list[TextContent]:
        """
        Route tool call to appropriate handler.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            role: User's role

        Returns:
            Tool response as MCP TextContent
        """
        try:
            # Route to appropriate handler
            handler = getattr(self, f"_handle_{tool_name}", None)
            if not handler:
                response = ToolResponse.error_response(
                    f"Unknown tool: {tool_name}",
                    "UNKNOWN_TOOL"
                )
            else:
                response = await handler(arguments, role)

            return [TextContent(
                type="text",
                text=response.model_dump_json(indent=2)
            )]

        except OktaMCPError as e:
            logger.error("tool_execution_error", tool=tool_name, error=str(e))
            return [TextContent(
                type="text",
                text=ToolResponse.error_response(
                    e.message,
                    e.error_code
                ).model_dump_json(indent=2)
            )]

    @trace_mcp_tool("list_users")
    async def _handle_list_users(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle list_users tool."""
        self.rbac.enforce_permission(role, "user", "read")

        # Try cache first
        cache_key = f"users:list:{arguments.get('query', '')}:{arguments.get('filter', '')}"
        cached = await self.cache.get(cache_key)
        if cached:
            return ToolResponse.success_response(cached, {"cached": True})

        users = await self.users_api.list_users(
            query=arguments.get("query"),
            filter_expr=arguments.get("filter"),
            limit=arguments.get("limit")
        )

        result = [user.model_dump() for user in users]

        # Cache result
        await self.cache.set(cache_key, result, ttl=300)

        return ToolResponse.success_response(result)

    @trace_mcp_tool("view_user_profile")
    async def _handle_view_user_profile(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle view_user_profile tool."""
        self.rbac.enforce_permission(role, "user", "read")

        user_id = arguments["user_id"]

        # Try cache first
        cache_key = f"user:{user_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return ToolResponse.success_response(cached, {"cached": True})

        user = await self.users_api.get_user(user_id)
        result = user.model_dump()

        # Cache result
        await self.cache.set(cache_key, result, ttl=300)

        return ToolResponse.success_response(result)

    @trace_mcp_tool("create_user_with_password")
    async def _handle_create_user_with_password(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle create_user_with_password tool."""
        self.rbac.enforce_permission(role, "user", "create")

        profile = OktaUserProfile(
            email=arguments["email"],
            login=arguments["email"],
            firstName=arguments["firstName"],
            lastName=arguments["lastName"]
        )

        user = await self.users_api.create_user(
            profile=profile,
            password=arguments["password"],
            activate=arguments.get("activate", True)
        )

        # Invalidate cache
        await self.cache.delete("users:list::")

        return ToolResponse.success_response(user.model_dump())

    @trace_mcp_tool("activate_user")
    async def _handle_activate_user(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle activate_user tool."""
        self.rbac.enforce_permission(role, "user", "activate")

        user_id = arguments["user_id"]
        send_email = arguments.get("send_email", True)

        result = await self.users_api.activate_user(user_id, send_email)

        # Invalidate cache
        await self.cache.delete(f"user:{user_id}")

        return ToolResponse.success_response(result)

    @trace_mcp_tool("deactivate_user")
    async def _handle_deactivate_user(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle deactivate_user tool."""
        self.rbac.enforce_permission(role, "user", "deactivate")

        user_id = arguments["user_id"]
        await self.users_api.deactivate_user(user_id)

        # Invalidate cache
        await self.cache.delete(f"user:{user_id}")

        return ToolResponse.success_response({"message": "User deactivated"})

    @trace_mcp_tool("suspend_user")
    async def _handle_suspend_user(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle suspend_user tool."""
        self.rbac.enforce_permission(role, "user", "suspend")

        user_id = arguments["user_id"]
        await self.users_api.suspend_user(user_id)

        # Invalidate cache
        await self.cache.delete(f"user:{user_id}")

        return ToolResponse.success_response({"message": "User suspended"})

    @trace_mcp_tool("unsuspend_user")
    async def _handle_unsuspend_user(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle unsuspend_user tool."""
        self.rbac.enforce_permission(role, "user", "suspend")

        user_id = arguments["user_id"]
        await self.users_api.unsuspend_user(user_id)

        # Invalidate cache
        await self.cache.delete(f"user:{user_id}")

        return ToolResponse.success_response({"message": "User unsuspended"})

    @trace_mcp_tool("unlock_user")
    async def _handle_unlock_user(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle unlock_user tool."""
        self.rbac.enforce_permission(role, "user", "unlock")

        user_id = arguments["user_id"]
        await self.users_api.unlock_user(user_id)

        # Invalidate cache
        await self.cache.delete(f"user:{user_id}")

        return ToolResponse.success_response({"message": "User unlocked"})

    @trace_mcp_tool("reset_password")
    async def _handle_reset_password(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle reset_password tool."""
        self.rbac.enforce_permission(role, "user", "reset_password")

        user_id = arguments["user_id"]
        send_email = arguments.get("send_email", True)

        result = await self.users_api.reset_password(user_id, send_email)

        return ToolResponse.success_response(result)

    @trace_mcp_tool("view_user_groups")
    async def _handle_view_user_groups(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle view_user_groups tool."""
        self.rbac.enforce_permission(role, "group", "read")

        user_id = arguments["user_id"]

        # Try cache first
        cache_key = f"user:{user_id}:groups"
        cached = await self.cache.get(cache_key)
        if cached:
            return ToolResponse.success_response(cached, {"cached": True})

        groups = await self.users_api.get_user_groups(user_id)

        # Cache result
        await self.cache.set(cache_key, groups, ttl=300)

        return ToolResponse.success_response(groups)

    @trace_mcp_tool("terminate_user")
    async def _handle_terminate_user(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle terminate_user tool."""
        self.rbac.enforce_permission(role, "user", "terminate")

        user_id = arguments["user_id"]
        await self.users_api.delete_user(user_id)

        # Invalidate cache
        await self.cache.delete(f"user:{user_id}")
        await self.cache.delete("users:list::")

        return ToolResponse.success_response({"message": "User terminated"})
