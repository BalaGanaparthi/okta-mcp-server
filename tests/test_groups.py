"""
Tests for group management functionality.
"""

import pytest
import respx
from httpx import Response

from okta.groups import OktaGroupsAPI
from okta.client import OktaClient


@pytest.fixture
def groups_api(okta_client: OktaClient) -> OktaGroupsAPI:
    """Create groups API instance."""
    return OktaGroupsAPI(okta_client)


@pytest.mark.asyncio
@respx.mock
async def test_list_groups(groups_api: OktaGroupsAPI, okta_client: OktaClient):
    """Test listing groups."""
    mock_groups = [
        {
            "id": "group1",
            "created": "2024-01-01T00:00:00.000Z",
            "lastUpdated": "2024-01-01T00:00:00.000Z",
            "type": "OKTA_GROUP",
            "profile": {
                "name": "Developers",
                "description": "Development team"
            }
        }
    ]

    respx.get(f"{okta_client.base_url}/groups").mock(
        return_value=Response(200, json=mock_groups)
    )

    groups = await groups_api.list_groups()

    assert len(groups) == 1
    assert groups[0].id == "group1"
    assert groups[0].profile["name"] == "Developers"


@pytest.mark.asyncio
@respx.mock
async def test_get_group(groups_api: OktaGroupsAPI, okta_client: OktaClient):
    """Test getting a single group."""
    mock_group = {
        "id": "group123",
        "created": "2024-01-01T00:00:00.000Z",
        "lastUpdated": "2024-01-01T00:00:00.000Z",
        "type": "OKTA_GROUP",
        "profile": {
            "name": "Admins",
            "description": "Administrator group"
        }
    }

    respx.get(f"{okta_client.base_url}/groups/group123").mock(
        return_value=Response(200, json=mock_group)
    )

    group = await groups_api.get_group("group123")

    assert group.id == "group123"
    assert group.profile["name"] == "Admins"


@pytest.mark.asyncio
@respx.mock
async def test_create_group(groups_api: OktaGroupsAPI, okta_client: OktaClient):
    """Test creating a group."""
    mock_response = {
        "id": "new_group",
        "created": "2024-01-01T00:00:00.000Z",
        "lastUpdated": "2024-01-01T00:00:00.000Z",
        "type": "OKTA_GROUP",
        "profile": {
            "name": "Test Group",
            "description": "Test description"
        }
    }

    respx.post(f"{okta_client.base_url}/groups").mock(
        return_value=Response(200, json=mock_response)
    )

    group = await groups_api.create_group(
        name="Test Group",
        description="Test description"
    )

    assert group.id == "new_group"
    assert group.profile["name"] == "Test Group"


@pytest.mark.asyncio
@respx.mock
async def test_update_group(groups_api: OktaGroupsAPI, okta_client: OktaClient):
    """Test updating a group."""
    mock_response = {
        "id": "group123",
        "created": "2024-01-01T00:00:00.000Z",
        "lastUpdated": "2024-01-01T00:00:00.000Z",
        "type": "OKTA_GROUP",
        "profile": {
            "name": "Updated Group",
            "description": "Updated description"
        }
    }

    respx.put(f"{okta_client.base_url}/groups/group123").mock(
        return_value=Response(200, json=mock_response)
    )

    group = await groups_api.update_group(
        "group123",
        name="Updated Group",
        description="Updated description"
    )

    assert group.profile["name"] == "Updated Group"


@pytest.mark.asyncio
@respx.mock
async def test_delete_group(groups_api: OktaGroupsAPI, okta_client: OktaClient):
    """Test deleting a group."""
    respx.delete(f"{okta_client.base_url}/groups/group123").mock(
        return_value=Response(204)
    )

    await groups_api.delete_group("group123")
    # Should complete without error


@pytest.mark.asyncio
@respx.mock
async def test_add_user_to_group(groups_api: OktaGroupsAPI, okta_client: OktaClient):
    """Test adding user to group."""
    respx.put(f"{okta_client.base_url}/groups/group123/users/user456").mock(
        return_value=Response(204)
    )

    await groups_api.add_user_to_group("group123", "user456")
    # Should complete without error


@pytest.mark.asyncio
@respx.mock
async def test_remove_user_from_group(groups_api: OktaGroupsAPI, okta_client: OktaClient):
    """Test removing user from group."""
    respx.delete(f"{okta_client.base_url}/groups/group123/users/user456").mock(
        return_value=Response(204)
    )

    await groups_api.remove_user_from_group("group123", "user456")
    # Should complete without error


@pytest.mark.asyncio
@respx.mock
async def test_list_group_members(groups_api: OktaGroupsAPI, okta_client: OktaClient):
    """Test listing group members."""
    mock_members = [
        {
            "id": "user1",
            "status": "ACTIVE",
            "profile": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@example.com"
            }
        }
    ]

    respx.get(f"{okta_client.base_url}/groups/group123/users").mock(
        return_value=Response(200, json=mock_members)
    )

    members = await groups_api.list_group_members("group123")

    assert len(members) == 1
    assert members[0]["id"] == "user1"
