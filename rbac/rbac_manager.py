"""
RBAC manager using Casbin for permission enforcement.

This module provides role-based access control using Casbin policies.
"""

import os
from typing import Optional
import casbin

from models.schemas import Role
from utils.logging import LoggerMixin
from utils.errors import RBACPermissionDenied, ConfigurationError


class RBACManager(LoggerMixin):
    """
    Role-Based Access Control manager.

    Uses Casbin to enforce access control policies.
    """

    def __init__(self, model_path: str, policy_path: str):
        """
        Initialize RBAC manager.

        Args:
            model_path: Path to Casbin model configuration
            policy_path: Path to Casbin policy CSV file

        Raises:
            ConfigurationError: If model or policy files not found
        """
        if not os.path.exists(model_path):
            raise ConfigurationError(
                f"RBAC model file not found: {model_path}",
                config_key="model_path"
            )

        if not os.path.exists(policy_path):
            raise ConfigurationError(
                f"RBAC policy file not found: {policy_path}",
                config_key="policy_path"
            )

        self.enforcer = casbin.Enforcer(model_path, policy_path)
        self.logger.info(
            "rbac_manager_initialized",
            model_path=model_path,
            policy_path=policy_path
        )

    def check_permission(
        self,
        role: Role,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if a role has permission to perform an action on a resource.

        Args:
            role: User's role
            resource: Resource type (e.g., 'user', 'group')
            action: Action to perform (e.g., 'create', 'read', 'delete')

        Returns:
            True if permission granted, False otherwise
        """
        has_permission = self.enforcer.enforce(role.value, resource, action)

        self.logger.info(
            "permission_check",
            role=role.value,
            resource=resource,
            action=action,
            granted=has_permission
        )

        return has_permission

    def enforce_permission(
        self,
        role: Role,
        resource: str,
        action: str
    ) -> None:
        """
        Enforce permission, raising exception if denied.

        Args:
            role: User's role
            resource: Resource type
            action: Action to perform

        Raises:
            RBACPermissionDenied: If permission is denied
        """
        if not self.check_permission(role, resource, action):
            self.logger.warning(
                "permission_denied",
                role=role.value,
                resource=resource,
                action=action
            )
            raise RBACPermissionDenied(
                role=role.value,
                resource=resource,
                action=action
            )

    def get_permissions_for_role(self, role: Role) -> list[list[str]]:
        """
        Get all permissions for a role.

        Args:
            role: Role to query

        Returns:
            List of permissions [resource, action]
        """
        # Get direct permissions
        permissions = self.enforcer.get_permissions_for_user(role.value)

        # Get permissions from parent roles (via role hierarchy)
        roles = self.enforcer.get_roles_for_user(role.value)
        for parent_role in roles:
            parent_permissions = self.enforcer.get_permissions_for_user(parent_role)
            permissions.extend(parent_permissions)

        # Remove duplicates and format
        unique_permissions = []
        seen = set()
        for perm in permissions:
            # perm format: [role, resource, action]
            if len(perm) >= 3:
                key = (perm[1], perm[2])  # (resource, action)
                if key not in seen:
                    seen.add(key)
                    unique_permissions.append([perm[1], perm[2]])

        return unique_permissions

    def get_all_roles(self) -> list[str]:
        """
        Get all defined roles.

        Returns:
            List of role names
        """
        all_subjects = self.enforcer.get_all_subjects()
        return list(set(all_subjects))

    def add_permission(
        self,
        role: Role,
        resource: str,
        action: str
    ) -> bool:
        """
        Add a permission for a role.

        Args:
            role: Role to grant permission to
            resource: Resource type
            action: Action to allow

        Returns:
            True if added successfully
        """
        result = self.enforcer.add_policy(role.value, resource, action)

        if result:
            self.logger.info(
                "permission_added",
                role=role.value,
                resource=resource,
                action=action
            )

        return result

    def remove_permission(
        self,
        role: Role,
        resource: str,
        action: str
    ) -> bool:
        """
        Remove a permission from a role.

        Args:
            role: Role to remove permission from
            resource: Resource type
            action: Action to deny

        Returns:
            True if removed successfully
        """
        result = self.enforcer.remove_policy(role.value, resource, action)

        if result:
            self.logger.info(
                "permission_removed",
                role=role.value,
                resource=resource,
                action=action
            )

        return result

    def reload_policy(self) -> None:
        """Reload policy from file."""
        self.enforcer.load_policy()
        self.logger.info("policy_reloaded")

    def save_policy(self) -> None:
        """Save current policy to file."""
        self.enforcer.save_policy()
        self.logger.info("policy_saved")


# Global RBAC manager instance
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """
    Get the global RBAC manager instance.

    Returns:
        RBACManager instance

    Raises:
        ConfigurationError: If RBAC manager not initialized
    """
    if _rbac_manager is None:
        raise ConfigurationError("RBAC manager not initialized")
    return _rbac_manager


def initialize_rbac_manager(model_path: str, policy_path: str) -> RBACManager:
    """
    Initialize the global RBAC manager.

    Args:
        model_path: Path to Casbin model file
        policy_path: Path to Casbin policy file

    Returns:
        Initialized RBAC manager
    """
    global _rbac_manager
    _rbac_manager = RBACManager(model_path, policy_path)
    return _rbac_manager
