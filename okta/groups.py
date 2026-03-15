"""
Okta Groups API operations.

This module provides high-level operations for managing Okta groups.
"""

from typing import Optional, List, Dict, Any

from okta.client import OktaClient
from models.schemas import OktaGroup, CreateGroupRequest, ModifyGroupRequest
from utils.logging import LoggerMixin
from utils.errors import ValidationError, ResourceNotFoundError


class OktaGroupsAPI(LoggerMixin):
    """High-level API for Okta group operations."""

    def __init__(self, client: OktaClient):
        """
        Initialize Groups API.

        Args:
            client: Okta API client
        """
        self.client = client

    async def list_groups(
        self,
        query: Optional[str] = None,
        filter_expr: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[OktaGroup]:
        """
        List groups with optional filtering.

        Args:
            query: Search query
            filter_expr: Okta filter expression
            limit: Maximum number of groups to return

        Returns:
            List of groups
        """
        self.logger.info("listing_groups", query=query, filter=filter_expr)

        params: Dict[str, Any] = {}
        if query:
            params["q"] = query
        if filter_expr:
            params["filter"] = filter_expr

        groups = []
        async for group_data in self.client.paginate("groups", params=params, limit=limit):
            groups.append(OktaGroup(**group_data))

        self.logger.info("groups_listed", count=len(groups))
        return groups

    async def get_group(self, group_id: str) -> OktaGroup:
        """
        Get a group by ID.

        Args:
            group_id: Group ID

        Returns:
            Group object

        Raises:
            ResourceNotFoundError: If group not found
        """
        self.logger.info("getting_group", group_id=group_id)

        try:
            group_data = await self.client.get(f"groups/{group_id}")
            group = OktaGroup(**group_data)
            self.logger.info("group_retrieved", group_id=group_id)
            return group
        except ResourceNotFoundError:
            raise ResourceNotFoundError("group", group_id)

    async def create_group(
        self,
        name: str,
        description: Optional[str] = None
    ) -> OktaGroup:
        """
        Create a new group.

        Args:
            name: Group name
            description: Group description

        Returns:
            Created group

        Raises:
            ValidationError: If name is invalid
        """
        self.logger.info("creating_group", name=name)

        if not name:
            raise ValidationError("Group name is required", field="name")

        payload = {
            "profile": {
                "name": name,
                "description": description or ""
            }
        }

        group_data = await self.client.post("groups", json=payload)
        group = OktaGroup(**group_data)

        self.logger.info("group_created", group_id=group.id, name=name)
        return group

    async def update_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> OktaGroup:
        """
        Update group profile.

        Args:
            group_id: Group ID
            name: New group name
            description: New group description

        Returns:
            Updated group
        """
        self.logger.info("updating_group", group_id=group_id)

        payload: Dict[str, Any] = {"profile": {}}

        if name is not None:
            payload["profile"]["name"] = name
        if description is not None:
            payload["profile"]["description"] = description

        group_data = await self.client.put(f"groups/{group_id}", json=payload)
        group = OktaGroup(**group_data)

        self.logger.info("group_updated", group_id=group_id)
        return group

    async def delete_group(self, group_id: str) -> None:
        """
        Delete a group.

        Args:
            group_id: Group ID
        """
        self.logger.info("deleting_group", group_id=group_id)

        await self.client.delete(f"groups/{group_id}")

        self.logger.info("group_deleted", group_id=group_id)

    async def add_user_to_group(self, group_id: str, user_id: str) -> None:
        """
        Add a user to a group.

        Args:
            group_id: Group ID
            user_id: User ID
        """
        self.logger.info(
            "adding_user_to_group",
            group_id=group_id,
            user_id=user_id
        )

        await self.client.put(f"groups/{group_id}/users/{user_id}")

        self.logger.info(
            "user_added_to_group",
            group_id=group_id,
            user_id=user_id
        )

    async def remove_user_from_group(self, group_id: str, user_id: str) -> None:
        """
        Remove a user from a group.

        Args:
            group_id: Group ID
            user_id: User ID
        """
        self.logger.info(
            "removing_user_from_group",
            group_id=group_id,
            user_id=user_id
        )

        await self.client.delete(f"groups/{group_id}/users/{user_id}")

        self.logger.info(
            "user_removed_from_group",
            group_id=group_id,
            user_id=user_id
        )

    async def list_group_members(
        self,
        group_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List members of a group.

        Args:
            group_id: Group ID
            limit: Maximum number of members to return

        Returns:
            List of user objects
        """
        self.logger.info("listing_group_members", group_id=group_id)

        members = []
        async for user_data in self.client.paginate(
            f"groups/{group_id}/users",
            limit=limit
        ):
            members.append(user_data)

        self.logger.info(
            "group_members_listed",
            group_id=group_id,
            count=len(members)
        )
        return members

    async def get_group_by_name(self, name: str) -> Optional[OktaGroup]:
        """
        Find a group by exact name match.

        Args:
            name: Group name to search for

        Returns:
            Group if found, None otherwise
        """
        self.logger.info("searching_group_by_name", name=name)

        # Use filter to search by name
        groups = await self.list_groups(query=name, limit=100)

        # Find exact match
        for group in groups:
            if group.profile.get("name") == name:
                self.logger.info("group_found_by_name", group_id=group.id, name=name)
                return group

        self.logger.info("group_not_found_by_name", name=name)
        return None
