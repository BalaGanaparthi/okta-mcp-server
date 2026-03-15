"""
OAuth 2.0 authentication flow for Okta.

This module implements the OAuth Authorization Code Flow for Okta,
including token exchange and refresh.
"""

from typing import Optional, Dict, Any
from urllib.parse import urlencode
import httpx
from datetime import datetime, timedelta

from config import OktaConfig
from utils.logging import LoggerMixin
from utils.errors import AuthenticationError
from models.schemas import Role


class OktaOAuthClient(LoggerMixin):
    """
    Okta OAuth 2.0 client.

    Handles OAuth flows including authorization, token exchange, and refresh.
    """

    def __init__(self, config: OktaConfig):
        """
        Initialize OAuth client.

        Args:
            config: Okta configuration
        """
        self.config = config
        self.base_url = f"https://{config.domain}"
        self.authorization_endpoint = f"{self.base_url}/oauth2/v1/authorize"
        self.token_endpoint = f"{self.base_url}/oauth2/v1/token"
        self.userinfo_endpoint = f"{self.base_url}/oauth2/v1/userinfo"
        self.introspect_endpoint = f"{self.base_url}/oauth2/v1/introspect"

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        scopes: Optional[list[str]] = None
    ) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            state: State parameter for CSRF protection
            scopes: OAuth scopes to request

        Returns:
            Authorization URL
        """
        default_scopes = ["openid", "profile", "email", "okta.users.read", "okta.groups.read"]
        scopes = scopes or default_scopes

        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(scopes),
        }

        if state:
            params["state"] = state

        url = f"{self.authorization_endpoint}?{urlencode(params)}"
        self.logger.info("authorization_url_generated", scopes=scopes)
        return url

    async def exchange_code_for_token(
        self,
        authorization_code: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Authorization code from callback

        Returns:
            Token response containing access_token, refresh_token, etc.

        Raises:
            AuthenticationError: If token exchange fails
        """
        self.logger.info("exchanging_code_for_token")

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0
                )

                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    self.logger.error(
                        "token_exchange_failed",
                        status_code=response.status_code,
                        error=error_data
                    )
                    raise AuthenticationError(
                        f"Token exchange failed: {error_data.get('error_description', 'Unknown error')}",
                        details=error_data
                    )

                token_data = response.json()
                self.logger.info(
                    "token_exchange_successful",
                    token_type=token_data.get("token_type")
                )
                return token_data

        except httpx.HTTPError as e:
            self.logger.error("token_exchange_http_error", error=str(e))
            raise AuthenticationError(
                f"HTTP error during token exchange: {str(e)}"
            ) from e

    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh an access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response

        Raises:
            AuthenticationError: If refresh fails
        """
        self.logger.info("refreshing_access_token")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0
                )

                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    self.logger.error(
                        "token_refresh_failed",
                        status_code=response.status_code,
                        error=error_data
                    )
                    raise AuthenticationError(
                        f"Token refresh failed: {error_data.get('error_description', 'Unknown error')}",
                        details=error_data
                    )

                token_data = response.json()
                self.logger.info("token_refresh_successful")
                return token_data

        except httpx.HTTPError as e:
            self.logger.error("token_refresh_http_error", error=str(e))
            raise AuthenticationError(
                f"HTTP error during token refresh: {str(e)}"
            ) from e

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information using access token.

        Args:
            access_token: OAuth access token

        Returns:
            User information from Okta

        Raises:
            AuthenticationError: If request fails
        """
        self.logger.info("fetching_user_info")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=30.0
                )

                if response.status_code != 200:
                    self.logger.error(
                        "userinfo_fetch_failed",
                        status_code=response.status_code
                    )
                    raise AuthenticationError("Failed to fetch user info")

                user_info = response.json()
                self.logger.info(
                    "userinfo_fetched",
                    user_id=user_info.get("sub")
                )
                return user_info

        except httpx.HTTPError as e:
            self.logger.error("userinfo_fetch_http_error", error=str(e))
            raise AuthenticationError(
                f"HTTP error fetching user info: {str(e)}"
            ) from e

    async def introspect_token(
        self,
        token: str,
        token_type_hint: str = "access_token"
    ) -> Dict[str, Any]:
        """
        Introspect a token to check validity and get metadata.

        Args:
            token: Token to introspect
            token_type_hint: Type of token (access_token or refresh_token)

        Returns:
            Token introspection data

        Raises:
            AuthenticationError: If introspection fails
        """
        data = {
            "token": token,
            "token_type_hint": token_type_hint,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.introspect_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0
                )

                if response.status_code != 200:
                    raise AuthenticationError("Token introspection failed")

                return response.json()

        except httpx.HTTPError as e:
            raise AuthenticationError(
                f"HTTP error during token introspection: {str(e)}"
            ) from e

    async def determine_user_role(
        self,
        access_token: str,
        user_info: Dict[str, Any]
    ) -> Role:
        """
        Determine user's role based on their Okta groups.

        Args:
            access_token: OAuth access token
            user_info: User information from Okta

        Returns:
            User's role
        """
        # This would typically query Okta groups and map them to roles
        # For now, return default role
        # TODO: Implement group-to-role mapping
        return Role.AGENT
