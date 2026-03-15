"""
Tests for authentication and session management.
"""

import pytest
from datetime import datetime, timedelta

from auth.session_store import SessionTokenStore
from auth.oauth import OktaOAuthClient
from models.schemas import Role
from utils.errors import SessionError


@pytest.mark.asyncio
async def test_create_session(session_store: SessionTokenStore):
    """Test session creation."""
    session_id = await session_store.create_session(
        access_token="test_token",
        user_id="user123",
        role=Role.ADMIN
    )

    assert session_id is not None
    assert len(session_id) > 0


@pytest.mark.asyncio
async def test_get_session(session_store: SessionTokenStore):
    """Test session retrieval."""
    session_id = await session_store.create_session(
        access_token="test_token",
        user_id="user123",
        role=Role.HELPDESK
    )

    session = await session_store.get_session(session_id)

    assert session is not None
    assert session.access_token == "test_token"
    assert session.user_id == "user123"
    assert session.role == Role.HELPDESK


@pytest.mark.asyncio
async def test_get_nonexistent_session(session_store: SessionTokenStore):
    """Test retrieving non-existent session."""
    session = await session_store.get_session("nonexistent")
    assert session is None


@pytest.mark.asyncio
async def test_get_access_token(session_store: SessionTokenStore):
    """Test getting access token from session."""
    session_id = await session_store.create_session(
        access_token="my_token",
        user_id="user123"
    )

    token = await session_store.get_access_token(session_id)
    assert token == "my_token"


@pytest.mark.asyncio
async def test_update_session(session_store: SessionTokenStore):
    """Test updating session."""
    session_id = await session_store.create_session(
        access_token="old_token",
        user_id="user123",
        role=Role.AGENT
    )

    await session_store.update_session(
        session_id,
        access_token="new_token",
        role=Role.ADMIN
    )

    session = await session_store.get_session(session_id)
    assert session.access_token == "new_token"
    assert session.role == Role.ADMIN


@pytest.mark.asyncio
async def test_update_nonexistent_session(session_store: SessionTokenStore):
    """Test updating non-existent session."""
    with pytest.raises(SessionError):
        await session_store.update_session("nonexistent", access_token="token")


@pytest.mark.asyncio
async def test_delete_session(session_store: SessionTokenStore):
    """Test session deletion."""
    session_id = await session_store.create_session(
        access_token="test_token",
        user_id="user123"
    )

    await session_store.delete_session(session_id)

    session = await session_store.get_session(session_id)
    assert session is None


@pytest.mark.asyncio
async def test_get_role(session_store: SessionTokenStore):
    """Test getting role from session."""
    session_id = await session_store.create_session(
        access_token="test_token",
        user_id="user123",
        role=Role.AUDITOR
    )

    role = await session_store.get_role(session_id)
    assert role == Role.AUDITOR


@pytest.mark.asyncio
async def test_session_count(session_store: SessionTokenStore):
    """Test session count."""
    initial_count = await session_store.get_session_count()

    await session_store.create_session("token1", user_id="user1")
    await session_store.create_session("token2", user_id="user2")

    final_count = await session_store.get_session_count()
    assert final_count == initial_count + 2


def test_oauth_authorization_url(test_config):
    """Test OAuth authorization URL generation."""
    oauth = OktaOAuthClient(test_config.okta)

    url = oauth.get_authorization_url(state="test_state")

    assert test_config.okta.domain in url
    assert test_config.okta.client_id in url
    assert "state=test_state" in url
    assert "response_type=code" in url
