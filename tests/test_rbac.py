"""
Tests for RBAC functionality.
"""

import pytest

from rbac.rbac_manager import RBACManager
from models.schemas import Role
from utils.errors import RBACPermissionDenied


def test_admin_has_all_permissions(rbac_manager: RBACManager):
    """Test that admin role has all permissions."""
    # Admin should be able to do everything
    assert rbac_manager.check_permission(Role.ADMIN, "user", "create")
    assert rbac_manager.check_permission(Role.ADMIN, "user", "read")
    assert rbac_manager.check_permission(Role.ADMIN, "user", "update")
    assert rbac_manager.check_permission(Role.ADMIN, "user", "delete")
    assert rbac_manager.check_permission(Role.ADMIN, "group", "create")
    assert rbac_manager.check_permission(Role.ADMIN, "group", "delete")


def test_helpdesk_user_permissions(rbac_manager: RBACManager):
    """Test helpdesk role permissions."""
    # Helpdesk can manage users
    assert rbac_manager.check_permission(Role.HELPDESK, "user", "create")
    assert rbac_manager.check_permission(Role.HELPDESK, "user", "read")
    assert rbac_manager.check_permission(Role.HELPDESK, "user", "update")

    # Helpdesk can read groups but not create/delete
    assert rbac_manager.check_permission(Role.HELPDESK, "group", "read")

    # Helpdesk cannot delete groups
    assert not rbac_manager.check_permission(Role.HELPDESK, "group", "delete")


def test_auditor_read_only(rbac_manager: RBACManager):
    """Test auditor role is read-only."""
    # Auditor can read
    assert rbac_manager.check_permission(Role.AUDITOR, "user", "read")
    assert rbac_manager.check_permission(Role.AUDITOR, "group", "read")

    # Auditor cannot create/update/delete
    assert not rbac_manager.check_permission(Role.AUDITOR, "user", "create")
    assert not rbac_manager.check_permission(Role.AUDITOR, "user", "update")
    assert not rbac_manager.check_permission(Role.AUDITOR, "user", "delete")
    assert not rbac_manager.check_permission(Role.AUDITOR, "group", "create")


def test_agent_limited_access(rbac_manager: RBACManager):
    """Test agent role has limited access."""
    # Agent can only read
    assert rbac_manager.check_permission(Role.AGENT, "user", "read")
    assert rbac_manager.check_permission(Role.AGENT, "group", "read")

    # Agent cannot create/update/delete
    assert not rbac_manager.check_permission(Role.AGENT, "user", "create")
    assert not rbac_manager.check_permission(Role.AGENT, "group", "delete")


def test_enforce_permission_success(rbac_manager: RBACManager):
    """Test successful permission enforcement."""
    # Should not raise exception
    rbac_manager.enforce_permission(Role.ADMIN, "user", "create")


def test_enforce_permission_denied(rbac_manager: RBACManager):
    """Test permission denial enforcement."""
    with pytest.raises(RBACPermissionDenied) as exc_info:
        rbac_manager.enforce_permission(Role.AGENT, "user", "create")

    assert "agent" in str(exc_info.value)
    assert "user" in str(exc_info.value)
    assert "create" in str(exc_info.value)


def test_get_permissions_for_role(rbac_manager: RBACManager):
    """Test getting all permissions for a role."""
    permissions = rbac_manager.get_permissions_for_role(Role.ADMIN)

    assert len(permissions) > 0
    assert ["user", "create"] in permissions
    assert ["group", "delete"] in permissions


def test_get_all_roles(rbac_manager: RBACManager):
    """Test getting all defined roles."""
    roles = rbac_manager.get_all_roles()

    assert "admin" in roles
    assert "helpdesk" in roles
    assert "auditor" in roles
    assert "agent" in roles
