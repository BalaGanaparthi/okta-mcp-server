"""
Custom exception classes for the Okta MCP Server.

This module defines all custom exceptions used throughout the application.
"""

from typing import Optional, Any


class OktaMCPError(Exception):
    """Base exception for all Okta MCP errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize the error.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """
        Convert error to dictionary format.

        Returns:
            Dictionary representation of the error
        """
        return {
            "success": False,
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class OktaAPIError(OktaMCPError):
    """Error communicating with Okta API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize Okta API error.

        Args:
            message: Error message
            status_code: HTTP status code from Okta
            error_code: Okta error code
            details: Additional error details
        """
        super().__init__(message, error_code, details)
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with status code."""
        result = super().to_dict()
        if self.status_code:
            result["status_code"] = self.status_code
        return result


class RBACPermissionDenied(OktaMCPError):
    """Permission denied by RBAC policy."""

    def __init__(
        self,
        role: str,
        resource: str,
        action: str,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize permission denied error.

        Args:
            role: User's role
            resource: Requested resource
            action: Requested action
            details: Additional details
        """
        message = f"Role '{role}' does not have permission to '{action}' on '{resource}'"
        super().__init__(message, "PERMISSION_DENIED", details)
        self.role = role
        self.resource = resource
        self.action = action


class AuthenticationError(OktaMCPError):
    """Authentication failed."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize authentication error.

        Args:
            message: Error message
            details: Additional details
        """
        super().__init__(message, "AUTHENTICATION_FAILED", details)


class ValidationError(OktaMCPError):
    """Input validation failed."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            details: Additional details
        """
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, "VALIDATION_ERROR", details)


class CacheError(OktaMCPError):
    """Cache operation failed."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize cache error.

        Args:
            message: Error message
            operation: Cache operation that failed
            details: Additional details
        """
        details = details or {}
        if operation:
            details["operation"] = operation
        super().__init__(message, "CACHE_ERROR", details)


class SessionError(OktaMCPError):
    """Session management error."""

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize session error.

        Args:
            message: Error message
            session_id: Session identifier
            details: Additional details
        """
        details = details or {}
        if session_id:
            details["session_id"] = session_id
        super().__init__(message, "SESSION_ERROR", details)


class ConfigurationError(OktaMCPError):
    """Configuration error."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize configuration error.

        Args:
            message: Error message
            config_key: Configuration key that caused error
            details: Additional details
        """
        details = details or {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, "CONFIGURATION_ERROR", details)


class RateLimitError(OktaAPIError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            details: Additional details
        """
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, 429, "RATE_LIMIT_EXCEEDED", details)
        self.retry_after = retry_after


class ResourceNotFoundError(OktaAPIError):
    """Requested resource not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize resource not found error.

        Args:
            resource_type: Type of resource (user, group, etc.)
            resource_id: Resource identifier
            details: Additional details
        """
        message = f"{resource_type.capitalize()} '{resource_id}' not found"
        details = details or {}
        details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        super().__init__(message, 404, "RESOURCE_NOT_FOUND", details)
