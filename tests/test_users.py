"""
Tests for user management functionality.
"""

import pytest
import respx
from httpx import Response

from okta.users import OktaUsersAPI
from okta.client import OktaClient
from models.schemas import OktaUserProfile, UserStatus


@pytest.fixture
def users_api(okta_client: OktaClient) -> OktaUsersAPI:
    """Create users API instance."""
    return OktaUsersAPI(okta_client)


@pytest.mark.asyncio
@respx.mock
async def test_list_users(users_api: OktaUsersAPI, okta_client: OktaClient):
    """Test listing users."""
    mock_users = [
        {
            "id": "user1",
            "status": "ACTIVE",
            "created": "2024-01-01T00:00:00.000Z",
            "lastUpdated": "2024-01-01T00:00:00.000Z",
            "profile": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@example.com",
                "login": "john@example.com"
            }
        }
    ]

    respx.get(f"{okta_client.base_url}/users").mock(
        return_value=Response(200, json=mock_users)
    )

    users = await users_api.list_users()

    assert len(users) == 1
    assert users[0].id == "user1"
    assert users[0].profile.firstName == "John"


@pytest.mark.asyncio
@respx.mock
async def test_get_user(users_api: OktaUsersAPI, okta_client: OktaClient):
    """Test getting a single user."""
    mock_user = {
        "id": "user123",
        "status": "ACTIVE",
        "created": "2024-01-01T00:00:00.000Z",
        "lastUpdated": "2024-01-01T00:00:00.000Z",
        "profile": {
            "firstName": "Jane",
            "lastName": "Smith",
            "email": "jane@example.com",
            "login": "jane@example.com"
        }
    }

    respx.get(f"{okta_client.base_url}/users/user123").mock(
        return_value=Response(200, json=mock_user)
    )

    user = await users_api.get_user("user123")

    assert user.id == "user123"
    assert user.profile.firstName == "Jane"
    assert user.status == UserStatus.ACTIVE


@pytest.mark.asyncio
@respx.mock
async def test_create_user(users_api: OktaUsersAPI, okta_client: OktaClient):
    """Test creating a user."""
    profile = OktaUserProfile(
        firstName="Test",
        lastName="User",
        email="test@example.com",
        login="test@example.com"
    )

    mock_response = {
        "id": "new_user",
        "status": "STAGED",
        "created": "2024-01-01T00:00:00.000Z",
        "lastUpdated": "2024-01-01T00:00:00.000Z",
        "profile": profile.model_dump()
    }

    respx.post(f"{okta_client.base_url}/users").mock(
        return_value=Response(200, json=mock_response)
    )

    user = await users_api.create_user(profile, password="Test123!", activate=False)

    assert user.id == "new_user"
    assert user.profile.email == "test@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_update_user(users_api: OktaUsersAPI, okta_client: OktaClient):
    """Test updating user profile."""
    mock_response = {
        "id": "user123",
        "status": "ACTIVE",
        "created": "2024-01-01T00:00:00.000Z",
        "lastUpdated": "2024-01-01T00:00:00.000Z",
        "profile": {
            "firstName": "Updated",
            "lastName": "Name",
            "email": "updated@example.com",
            "login": "updated@example.com"
        }
    }

    respx.put(f"{okta_client.base_url}/users/user123").mock(
        return_value=Response(200, json=mock_response)
    )

    user = await users_api.update_user(
        "user123",
        {"firstName": "Updated", "lastName": "Name"}
    )

    assert user.profile.firstName == "Updated"


@pytest.mark.asyncio
@respx.mock
async def test_activate_user(users_api: OktaUsersAPI, okta_client: OktaClient):
    """Test activating a user."""
    mock_response = {"activationUrl": "https://example.okta.com/activate"}

    respx.post(f"{okta_client.base_url}/users/user123/lifecycle/activate").mock(
        return_value=Response(200, json=mock_response)
    )

    result = await users_api.activate_user("user123", send_email=True)

    assert "activationUrl" in result


@pytest.mark.asyncio
@respx.mock
async def test_suspend_user(users_api: OktaUsersAPI, okta_client: OktaClient):
    """Test suspending a user."""
    respx.post(f"{okta_client.base_url}/users/user123/lifecycle/suspend").mock(
        return_value=Response(200, json={})
    )

    await users_api.suspend_user("user123")
    # Should complete without error
