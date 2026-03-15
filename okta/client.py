"""
Async Okta API client with retry logic, rate limiting, and pagination.

This module provides a robust HTTP client for interacting with the Okta Management API.
"""

import asyncio
from typing import Optional, Dict, Any, AsyncIterator
from urllib.parse import parse_qs, urlparse
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config import OktaConfig
from utils.logging import LoggerMixin
from utils.errors import OktaAPIError, RateLimitError, ResourceNotFoundError


class OktaClient(LoggerMixin):
    """
    Async HTTP client for Okta Management API.

    Features:
    - Automatic retries with exponential backoff
    - Rate limit handling
    - Pagination support
    - Request/response logging
    """

    def __init__(
        self,
        config: OktaConfig,
        access_token: Optional[str] = None
    ):
        """
        Initialize Okta client.

        Args:
            config: Okta configuration
            access_token: OAuth access token (optional, will use API token if not provided)
        """
        self.config = config
        self.base_url = f"https://{config.domain}/api/v1"
        self.access_token = access_token
        self.api_token = config.api_token
        self.client = httpx.AsyncClient(timeout=30.0)
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset: Optional[int] = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _get_auth_header(self) -> str:
        """
        Get authorization header value.

        Returns:
            Authorization header value
        """
        if self.access_token:
            return f"Bearer {self.access_token}"
        elif self.api_token:
            return f"SSWS {self.api_token}"
        else:
            raise OktaAPIError("No authentication token available")

    def _update_rate_limit_info(self, headers: httpx.Headers) -> None:
        """
        Update rate limit information from response headers.

        Args:
            headers: Response headers
        """
        if "x-rate-limit-remaining" in headers:
            self._rate_limit_remaining = int(headers["x-rate-limit-remaining"])
        if "x-rate-limit-reset" in headers:
            self._rate_limit_reset = int(headers["x-rate-limit-reset"])

        if self._rate_limit_remaining is not None:
            self.logger.debug(
                "rate_limit_info",
                remaining=self._rate_limit_remaining,
                reset=self._rate_limit_reset
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to Okta API.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            json: JSON body
            headers: Additional headers

        Returns:
            Response JSON

        Raises:
            OktaAPIError: If request fails
            RateLimitError: If rate limit exceeded
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        request_headers = {
            "Authorization": self._get_auth_header(),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if headers:
            request_headers.update(headers)

        self.logger.info(
            "okta_api_request",
            method=method,
            endpoint=endpoint,
            params=params
        )

        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=request_headers
            )

            self._update_rate_limit_info(response.headers)

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("x-rate-limit-reset", 60))
                self.logger.warning(
                    "rate_limit_exceeded",
                    retry_after=retry_after
                )
                raise RateLimitError(retry_after=retry_after)

            # Handle not found
            if response.status_code == 404:
                error_data = response.json() if response.text else {}
                raise ResourceNotFoundError(
                    resource_type="resource",
                    resource_id=endpoint,
                    details=error_data
                )

            # Handle other errors
            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("errorSummary", f"HTTP {response.status_code}")
                self.logger.error(
                    "okta_api_error",
                    status_code=response.status_code,
                    error=error_data
                )
                raise OktaAPIError(
                    message=error_msg,
                    status_code=response.status_code,
                    error_code=error_data.get("errorCode"),
                    details=error_data
                )

            # Return JSON response or empty dict for 204 No Content
            if response.status_code == 204:
                return {}

            result = response.json()
            self.logger.info(
                "okta_api_response",
                status_code=response.status_code,
                endpoint=endpoint
            )
            return result

        except httpx.HTTPError as e:
            self.logger.error(
                "okta_api_http_error",
                error=str(e),
                endpoint=endpoint
            )
            raise OktaAPIError(f"HTTP error: {str(e)}") from e

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response JSON
        """
        return await self.request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint
            json: JSON body
            params: Query parameters

        Returns:
            Response JSON
        """
        return await self.request("POST", endpoint, json=json, params=params)

    async def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a PUT request.

        Args:
            endpoint: API endpoint
            json: JSON body

        Returns:
            Response JSON
        """
        return await self.request("PUT", endpoint, json=json)

    async def delete(
        self,
        endpoint: str
    ) -> Dict[str, Any]:
        """
        Make a DELETE request.

        Args:
            endpoint: API endpoint

        Returns:
            Response JSON
        """
        return await self.request("DELETE", endpoint)

    async def paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Paginate through API results.

        Args:
            endpoint: API endpoint
            params: Query parameters
            limit: Maximum number of items to return

        Yields:
            Individual items from paginated responses
        """
        params = params or {}
        params.setdefault("limit", 200)  # Okta default page size

        count = 0
        url = endpoint

        while url:
            response = await self.client.get(
                f"{self.base_url}/{url.lstrip('/')}",
                params=params if url == endpoint else None,
                headers={
                    "Authorization": self._get_auth_header(),
                    "Accept": "application/json"
                }
            )

            self._update_rate_limit_info(response.headers)

            if response.status_code != 200:
                raise OktaAPIError(
                    f"Pagination request failed",
                    status_code=response.status_code
                )

            items = response.json()

            for item in items:
                yield item
                count += 1
                if limit and count >= limit:
                    return

            # Get next page URL from Link header
            link_header = response.headers.get("link", "")
            url = self._parse_next_link(link_header)
            params = None  # Don't send params for subsequent requests

    def _parse_next_link(self, link_header: str) -> Optional[str]:
        """
        Parse the next link from Link header.

        Args:
            link_header: Link header value

        Returns:
            Next page URL or None if no next page
        """
        if not link_header:
            return None

        links = link_header.split(",")
        for link in links:
            if 'rel="next"' in link:
                url = link.split(";")[0].strip("<> ")
                # Extract just the path and query
                parsed = urlparse(url)
                return f"{parsed.path}?{parsed.query}" if parsed.query else parsed.path

        return None
