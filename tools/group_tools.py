"""
MCP tools for Okta group management.

This module defines all MCP tools for managing groups in Okta.
"""

from typing import Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent

from okta.client import OktaClient
from okta.groups import OktaGroupsAPI
from models.schemas import ToolResponse, Role
from rbac.rbac_manager import RBACManager
from cache.cache_manager import CacheManager
from telemetry.tracing import trace_mcp_tool
from utils.logging import get_logger
from utils.errors import OktaMCPError

logger = get_logger(__name__)


class GroupTools:
    """Collection of MCP tools for group management."""

    def __init__(
        self,
        okta_client: OktaClient,
        rbac_manager: RBACManager,
        cache_manager: CacheManager
    ):
        """
        Initialize group tools.

        Args:
            okta_client: Okta API client
            rbac_manager: RBAC manager
            cache_manager: Cache manager
        """
        self.okta_client = okta_client
        self.groups_api = OktaGroupsAPI(okta_client)
        self.rbac = rbac_manager
        self.cache = cache_manager

    def register_tools(self, server: Server) -> None:
        """
        Register all group tools with MCP server.

        Args:
            server: MCP server instance
        """
        tools = [
            Tool(
                name="list_groups",
                description="List all Okta groups",
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
                name="view_group_details",
                description="View detailed group information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "string", "description": "Group ID"}
                    },
                    "required": ["group_id"]
                }
            ),
            Tool(
                name="create_group",
                description="Create a new group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Group name"},
                        "description": {"type": "string", "description": "Group description"}
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="modify_group",
                description="Modify group properties",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "string"},
                        "name": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["group_id"]
                }
            ),
            Tool(
                name="delete_group",
                description="Delete a group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "string"}
                    },
                    "required": ["group_id"]
                }
            ),
            Tool(
                name="add_user_to_group",
                description="Add a user to a group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "string"},
                        "user_id": {"type": "string"}
                    },
                    "required": ["group_id", "user_id"]
                }
            ),
            Tool(
                name="remove_user_from_group",
                description="Remove a user from a group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "string"},
                        "user_id": {"type": "string"}
                    },
                    "required": ["group_id", "user_id"]
                }
            ),
            Tool(
                name="list_users_in_group",
                description="List all members of a group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "string"},
                        "limit": {"type": "integer"}
                    },
                    "required": ["group_id"]
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

    @trace_mcp_tool("list_groups")
    async def _handle_list_groups(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle list_groups tool."""
        self.rbac.enforce_permission(role, "group", "read")

        # Try cache first
        cache_key = f"groups:list:{arguments.get('query', '')}:{arguments.get('filter', '')}"
        cached = await self.cache.get(cache_key)
        if cached:
            return ToolResponse.success_response(cached, {"cached": True})

        groups = await self.groups_api.list_groups(
            query=arguments.get("query"),
            filter_expr=arguments.get("filter"),
            limit=arguments.get("limit")
        )

        result = [group.model_dump() for group in groups]

        # Cache result
        await self.cache.set(cache_key, result, ttl=300)

        return ToolResponse.success_response(result)

    @trace_mcp_tool("view_group_details")
    async def _handle_view_group_details(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle view_group_details tool."""
        self.rbac.enforce_permission(role, "group", "read")

        group_id = arguments["group_id"]

        # Try cache first
        cache_key = f"group:{group_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return ToolResponse.success_response(cached, {"cached": True})

        group = await self.groups_api.get_group(group_id)
        result = group.model_dump()

        # Cache result
        await self.cache.set(cache_key, result, ttl=300)

        return ToolResponse.success_response(result)

    @trace_mcp_tool("create_group")
    async def _handle_create_group(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle create_group tool."""
        self.rbac.enforce_permission(role, "group", "create")

        group = await self.groups_api.create_group(
            name=arguments["name"],
            description=arguments.get("description")
        )

        # Invalidate cache
        await self.cache.delete("groups:list::")

        return ToolResponse.success_response(group.model_dump())

    @trace_mcp_tool("modify_group")
    async def _handle_modify_group(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle modify_group tool."""
        self.rbac.enforce_permission(role, "group", "update")

        group_id = arguments["group_id"]

        group = await self.groups_api.update_group(
            group_id=group_id,
            name=arguments.get("name"),
            description=arguments.get("description")
        )

        # Invalidate cache
        await self.cache.delete(f"group:{group_id}")
        await self.cache.delete("groups:list::")

        return ToolResponse.success_response(group.model_dump())

    @trace_mcp_tool("delete_group")
    async def _handle_delete_group(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle delete_group tool."""
        self.rbac.enforce_permission(role, "group", "delete")

        group_id = arguments["group_id"]
        await self.groups_api.delete_group(group_id)

        # Invalidate cache
        await self.cache.delete(f"group:{group_id}")
        await self.cache.delete("groups:list::")

        return ToolResponse.success_response({"message": "Group deleted"})

    @trace_mcp_tool("add_user_to_group")
    async def _handle_add_user_to_group(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle add_user_to_group tool."""
        self.rbac.enforce_permission(role, "group", "add_member")

        group_id = arguments["group_id"]
        user_id = arguments["user_id"]

        await self.groups_api.add_user_to_group(group_id, user_id)

        # Invalidate cache
        await self.cache.delete(f"group:{group_id}:members")
        await self.cache.delete(f"user:{user_id}:groups")

        return ToolResponse.success_response({
            "message": "User added to group",
            "group_id": group_id,
            "user_id": user_id
        })

    @trace_mcp_tool("remove_user_from_group")
    async def _handle_remove_user_from_group(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle remove_user_from_group tool."""
        self.rbac.enforce_permission(role, "group", "remove_member")

        group_id = arguments["group_id"]
        user_id = arguments["user_id"]

        await self.groups_api.remove_user_from_group(group_id, user_id)

        # Invalidate cache
        await self.cache.delete(f"group:{group_id}:members")
        await self.cache.delete(f"user:{user_id}:groups")

        return ToolResponse.success_response({
            "message": "User removed from group",
            "group_id": group_id,
            "user_id": user_id
        })

    @trace_mcp_tool("list_users_in_group")
    async def _handle_list_users_in_group(
        self,
        arguments: Dict[str, Any],
        role: Role
    ) -> ToolResponse:
        """Handle list_users_in_group tool."""
        self.rbac.enforce_permission(role, "group", "read")

        group_id = arguments["group_id"]

        # Try cache first
        cache_key = f"group:{group_id}:members"
        cached = await self.cache.get(cache_key)
        if cached:
            return ToolResponse.success_response(cached, {"cached": True})

        members = await self.groups_api.list_group_members(
            group_id,
            limit=arguments.get("limit")
        )

        # Cache result
        await self.cache.set(cache_key, members, ttl=300)

        return ToolResponse.success_response(members)
