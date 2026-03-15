"""
Pydantic models and schemas for the Okta MCP Server.

This module defines all data models used throughout the application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserStatus(str, Enum):
    """Okta user status enumeration."""

    ACTIVE = "ACTIVE"
    STAGED = "STAGED"
    PROVISIONED = "PROVISIONED"
    RECOVERY = "RECOVERY"
    PASSWORD_EXPIRED = "PASSWORD_EXPIRED"
    LOCKED_OUT = "LOCKED_OUT"
    SUSPENDED = "SUSPENDED"
    DEPROVISIONED = "DEPROVISIONED"


class Role(str, Enum):
    """RBAC role enumeration."""

    ADMIN = "admin"
    HELPDESK = "helpdesk"
    AUDITOR = "auditor"
    AGENT = "agent"


class OktaUserProfile(BaseModel):
    """Okta user profile."""

    firstName: str = Field(..., description="User's first name")
    lastName: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    login: EmailStr = Field(..., description="User's login (usually email)")
    mobilePhone: Optional[str] = Field(None, description="Mobile phone number")
    secondEmail: Optional[EmailStr] = Field(None, description="Secondary email")
    manager: Optional[str] = Field(None, description="Manager's user ID")
    department: Optional[str] = Field(None, description="Department")
    title: Optional[str] = Field(None, description="Job title")

    model_config = ConfigDict(extra="allow")


class OktaUser(BaseModel):
    """Okta user object."""

    id: str = Field(..., description="User ID")
    status: UserStatus = Field(..., description="User status")
    created: datetime = Field(..., description="Creation timestamp")
    activated: Optional[datetime] = Field(None, description="Activation timestamp")
    statusChanged: Optional[datetime] = Field(None, description="Status change timestamp")
    lastLogin: Optional[datetime] = Field(None, description="Last login timestamp")
    lastUpdated: datetime = Field(..., description="Last update timestamp")
    passwordChanged: Optional[datetime] = Field(None, description="Password change timestamp")
    profile: OktaUserProfile = Field(..., description="User profile")

    model_config = ConfigDict(extra="allow")


class OktaGroup(BaseModel):
    """Okta group object."""

    id: str = Field(..., description="Group ID")
    created: datetime = Field(..., description="Creation timestamp")
    lastUpdated: datetime = Field(..., description="Last update timestamp")
    lastMembershipUpdated: Optional[datetime] = Field(
        None,
        description="Last membership update timestamp"
    )
    objectClass: list[str] = Field(default_factory=list, description="Object class")
    type: str = Field(..., description="Group type")
    profile: dict[str, Any] = Field(..., description="Group profile")

    model_config = ConfigDict(extra="allow")


class CreateUserRequest(BaseModel):
    """Request to create a new user."""

    profile: OktaUserProfile = Field(..., description="User profile")
    password: Optional[str] = Field(None, description="User password")
    activate: bool = Field(default=True, description="Activate user immediately")
    send_email: bool = Field(default=False, description="Send activation email")
    group_ids: Optional[list[str]] = Field(
        None,
        description="Group IDs to add user to"
    )


class ModifyUserRequest(BaseModel):
    """Request to modify a user."""

    profile: Optional[dict[str, Any]] = Field(None, description="Profile updates")
    password: Optional[str] = Field(None, description="New password")
    group_ids: Optional[list[str]] = Field(None, description="Group IDs to update")


class CreateGroupRequest(BaseModel):
    """Request to create a new group."""

    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    user_ids: Optional[list[str]] = Field(
        None,
        description="User IDs to add to group"
    )


class ModifyGroupRequest(BaseModel):
    """Request to modify a group."""

    name: Optional[str] = Field(None, description="New group name")
    description: Optional[str] = Field(None, description="New group description")


class SessionData(BaseModel):
    """Session data structure."""

    session_id: str = Field(..., description="Session identifier")
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration time")
    user_id: Optional[str] = Field(None, description="Okta user ID")
    role: Role = Field(default=Role.AGENT, description="User's role")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session creation time"
    )


class ToolResponse(BaseModel):
    """Standard tool response format."""

    success: bool = Field(..., description="Whether the operation succeeded")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )

    @classmethod
    def success_response(
        cls,
        data: Any,
        metadata: Optional[dict[str, Any]] = None
    ) -> "ToolResponse":
        """
        Create a success response.

        Args:
            data: Response data
            metadata: Additional metadata

        Returns:
            ToolResponse with success=True
        """
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def error_response(
        cls,
        error: str,
        error_code: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> "ToolResponse":
        """
        Create an error response.

        Args:
            error: Error message
            error_code: Error code
            metadata: Additional metadata

        Returns:
            ToolResponse with success=False
        """
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            metadata=metadata
        )


class CacheEntry(BaseModel):
    """Cache entry with metadata."""

    key: str = Field(..., description="Cache key")
    value: Any = Field(..., description="Cached value")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Cache entry creation time"
    )
    ttl: int = Field(..., description="Time to live in seconds")

    def is_expired(self) -> bool:
        """
        Check if cache entry is expired.

        Returns:
            True if expired, False otherwise
        """
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl
