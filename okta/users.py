"""
Okta Users API operations.

This module provides high-level operations for managing Okta users.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from okta.client import OktaClient
from models.schemas import (
    OktaUser,
    OktaUserProfile,
    CreateUserRequest,
    ModifyUserRequest,
    UserStatus
)
from utils.logging import LoggerMixin
from utils.errors import ValidationError, ResourceNotFoundError


class OktaUsersAPI(LoggerMixin):
    """High-level API for Okta user operations."""

    def __init__(self, client: OktaClient):
        """
        Initialize Users API.

        Args:
            client: Okta API client
        """
        self.client = client

    async def list_users(
        self,
        query: Optional[str] = None,
        limit: Optional[int] = None,
        filter_expr: Optional[str] = None
    ) -> List[OktaUser]:
        """
        List users with optional filtering.

        Args:
            query: Search query
            limit: Maximum number of users to return
            filter_expr: Okta filter expression

        Returns:
            List of users
        """
        self.logger.info("listing_users", query=query, filter=filter_expr)

        params: Dict[str, Any] = {}
        if query:
            params["q"] = query
        if filter_expr:
            params["filter"] = filter_expr

        users = []
        async for user_data in self.client.paginate("users", params=params, limit=limit):
            users.append(OktaUser(**user_data))

        self.logger.info("users_listed", count=len(users))
        return users

    async def get_user(self, user_id: str) -> OktaUser:
        """
        Get a user by ID.

        Args:
            user_id: User ID or login

        Returns:
            User object

        Raises:
            ResourceNotFoundError: If user not found
        """
        self.logger.info("getting_user", user_id=user_id)

        try:
            user_data = await self.client.get(f"users/{user_id}")
            user = OktaUser(**user_data)
            self.logger.info("user_retrieved", user_id=user_id)
            return user
        except ResourceNotFoundError:
            raise ResourceNotFoundError("user", user_id)

    async def create_user(
        self,
        profile: OktaUserProfile,
        password: Optional[str] = None,
        activate: bool = True,
        send_email: bool = False
    ) -> OktaUser:
        """
        Create a new user.

        Args:
            profile: User profile
            password: User password (optional)
            activate: Activate user immediately
            send_email: Send activation email

        Returns:
            Created user

        Raises:
            ValidationError: If profile is invalid
        """
        self.logger.info(
            "creating_user",
            email=profile.email,
            activate=activate
        )

        # Validate required fields
        if not profile.email or not profile.firstName or not profile.lastName:
            raise ValidationError("Email, firstName, and lastName are required")

        payload: Dict[str, Any] = {
            "profile": profile.model_dump(exclude_none=True)
        }

        if password:
            payload["credentials"] = {
                "password": {"value": password}
            }

        params = {
            "activate": str(activate).lower(),
            "sendEmail": str(send_email).lower()
        }

        user_data = await self.client.post("users", json=payload, params=params)
        user = OktaUser(**user_data)

        self.logger.info("user_created", user_id=user.id, email=profile.email)
        return user

    async def update_user(
        self,
        user_id: str,
        profile_updates: Dict[str, Any]
    ) -> OktaUser:
        """
        Update user profile.

        Args:
            user_id: User ID
            profile_updates: Profile fields to update

        Returns:
            Updated user
        """
        self.logger.info("updating_user", user_id=user_id)

        payload = {"profile": profile_updates}
        user_data = await self.client.put(f"users/{user_id}", json=payload)
        user = OktaUser(**user_data)

        self.logger.info("user_updated", user_id=user_id)
        return user

    async def delete_user(self, user_id: str, send_email: bool = False) -> None:
        """
        Delete (deactivate) a user.

        Args:
            user_id: User ID
            send_email: Send deactivation email
        """
        self.logger.info("deleting_user", user_id=user_id)

        # First deactivate
        await self.deactivate_user(user_id)

        # Then delete
        params = {"sendEmail": str(send_email).lower()}
        await self.client.delete(f"users/{user_id}")

        self.logger.info("user_deleted", user_id=user_id)

    async def activate_user(
        self,
        user_id: str,
        send_email: bool = True
    ) -> Dict[str, Any]:
        """
        Activate a user.

        Args:
            user_id: User ID
            send_email: Send activation email

        Returns:
            Activation result
        """
        self.logger.info("activating_user", user_id=user_id)

        params = {"sendEmail": str(send_email).lower()}
        result = await self.client.post(
            f"users/{user_id}/lifecycle/activate",
            params=params
        )

        self.logger.info("user_activated", user_id=user_id)
        return result

    async def deactivate_user(self, user_id: str, send_email: bool = False) -> None:
        """
        Deactivate a user.

        Args:
            user_id: User ID
            send_email: Send deactivation email
        """
        self.logger.info("deactivating_user", user_id=user_id)

        params = {"sendEmail": str(send_email).lower()}
        await self.client.post(f"users/{user_id}/lifecycle/deactivate", params=params)

        self.logger.info("user_deactivated", user_id=user_id)

    async def suspend_user(self, user_id: str) -> None:
        """
        Suspend a user.

        Args:
            user_id: User ID
        """
        self.logger.info("suspending_user", user_id=user_id)

        await self.client.post(f"users/{user_id}/lifecycle/suspend")

        self.logger.info("user_suspended", user_id=user_id)

    async def unsuspend_user(self, user_id: str) -> None:
        """
        Unsuspend a user.

        Args:
            user_id: User ID
        """
        self.logger.info("unsuspending_user", user_id=user_id)

        await self.client.post(f"users/{user_id}/lifecycle/unsuspend")

        self.logger.info("user_unsuspended", user_id=user_id)

    async def unlock_user(self, user_id: str) -> None:
        """
        Unlock a locked user.

        Args:
            user_id: User ID
        """
        self.logger.info("unlocking_user", user_id=user_id)

        await self.client.post(f"users/{user_id}/lifecycle/unlock")

        self.logger.info("user_unlocked", user_id=user_id)

    async def reset_password(
        self,
        user_id: str,
        send_email: bool = True
    ) -> Dict[str, Any]:
        """
        Reset user password.

        Args:
            user_id: User ID
            send_email: Send password reset email

        Returns:
            Reset result with temporary password or reset URL
        """
        self.logger.info("resetting_password", user_id=user_id)

        params = {"sendEmail": str(send_email).lower()}
        result = await self.client.post(
            f"users/{user_id}/lifecycle/reset_password",
            params=params
        )

        self.logger.info("password_reset", user_id=user_id)
        return result

    async def expire_password(self, user_id: str, temp_password: bool = False) -> OktaUser:
        """
        Expire user password (force password change).

        Args:
            user_id: User ID
            temp_password: Generate temporary password

        Returns:
            Updated user
        """
        self.logger.info("expiring_password", user_id=user_id)

        params = {"tempPassword": str(temp_password).lower()}
        user_data = await self.client.post(
            f"users/{user_id}/lifecycle/expire_password",
            params=params
        )

        user = OktaUser(**user_data)
        self.logger.info("password_expired", user_id=user_id)
        return user

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """
        Change user password (requires old password).

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            Change result
        """
        self.logger.info("changing_password", user_id=user_id)

        payload = {
            "oldPassword": {"value": old_password},
            "newPassword": {"value": new_password}
        }

        result = await self.client.post(
            f"users/{user_id}/credentials/change_password",
            json=payload
        )

        self.logger.info("password_changed", user_id=user_id)
        return result

    async def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get groups a user belongs to.

        Args:
            user_id: User ID

        Returns:
            List of groups
        """
        self.logger.info("getting_user_groups", user_id=user_id)

        groups = []
        async for group_data in self.client.paginate(f"users/{user_id}/groups"):
            groups.append(group_data)

        self.logger.info("user_groups_retrieved", user_id=user_id, count=len(groups))
        return groups
