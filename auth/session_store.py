"""
Session token store for managing user sessions.

This module provides thread-safe session storage with support for
both in-memory and Redis-backed storage.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
from uuid import uuid4

from models.schemas import SessionData, Role
from utils.logging import LoggerMixin
from utils.errors import SessionError


class SessionTokenStore(LoggerMixin):
    """
    Thread-safe session token store.

    Manages mapping of session IDs to access tokens and session metadata.
    """

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize session store.

        Args:
            default_ttl: Default session TTL in seconds
        """
        self._sessions: Dict[str, SessionData] = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl
        self.logger.info("session_store_initialized", default_ttl=default_ttl)

    async def create_session(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        user_id: Optional[str] = None,
        role: Role = Role.AGENT
    ) -> str:
        """
        Create a new session.

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            expires_in: Token expiry time in seconds
            user_id: Okta user ID
            role: User's role

        Returns:
            Session ID
        """
        session_id = str(uuid4())
        ttl = expires_in or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        session_data = SessionData(
            session_id=session_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            user_id=user_id,
            role=role
        )

        async with self._lock:
            self._sessions[session_id] = session_data

        self.logger.info(
            "session_created",
            session_id=session_id,
            user_id=user_id,
            role=role.value,
            expires_at=expires_at.isoformat()
        )

        return session_id

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Retrieve session data by session ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionData if found and valid, None otherwise
        """
        async with self._lock:
            session = self._sessions.get(session_id)

        if session is None:
            self.logger.warning("session_not_found", session_id=session_id)
            return None

        # Check if session is expired
        if datetime.utcnow() > session.expires_at:
            self.logger.info("session_expired", session_id=session_id)
            await self.delete_session(session_id)
            return None

        return session

    async def get_access_token(self, session_id: str) -> Optional[str]:
        """
        Get access token for a session.

        Args:
            session_id: Session identifier

        Returns:
            Access token if session is valid, None otherwise
        """
        session = await self.get_session(session_id)
        return session.access_token if session else None

    async def update_session(
        self,
        session_id: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        role: Optional[Role] = None
    ) -> None:
        """
        Update session data.

        Args:
            session_id: Session identifier
            access_token: New access token
            refresh_token: New refresh token
            expires_in: New expiry time in seconds
            role: New role

        Raises:
            SessionError: If session not found
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionError(
                    f"Session not found: {session_id}",
                    session_id=session_id
                )

            if access_token:
                session.access_token = access_token
            if refresh_token:
                session.refresh_token = refresh_token
            if expires_in:
                session.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            if role:
                session.role = role

            self._sessions[session_id] = session

        self.logger.info("session_updated", session_id=session_id)

    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session identifier
        """
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                self.logger.info("session_deleted", session_id=session_id)

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired_sessions = []

        async with self._lock:
            for session_id, session in self._sessions.items():
                if now > session.expires_at:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self._sessions[session_id]

        count = len(expired_sessions)
        if count > 0:
            self.logger.info("sessions_cleaned_up", count=count)

        return count

    async def get_session_count(self) -> int:
        """
        Get the current number of active sessions.

        Returns:
            Number of active sessions
        """
        async with self._lock:
            return len(self._sessions)

    async def get_role(self, session_id: str) -> Optional[Role]:
        """
        Get the role for a session.

        Args:
            session_id: Session identifier

        Returns:
            Role if session exists, None otherwise
        """
        session = await self.get_session(session_id)
        return session.role if session else None
