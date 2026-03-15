"""
Pytest configuration and fixtures.

This module provides common fixtures for testing.
"""

import pytest
import asyncio
from typing import AsyncGenerator

from config import (
    Config, OktaConfig, RedisConfig, CacheConfig,
    RBACConfig, ServerConfig, OTelConfig, SecurityConfig
)
from okta.client import OktaClient
from cache.cache_manager import CacheManager
from rbac.rbac_manager import RBACManager
from auth.session_store import SessionTokenStore


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config() -> Config:
    """Create test configuration."""
    return Config(
        okta=OktaConfig(
            domain="test.okta.com",
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            api_token="test_api_token"
        ),
        redis=RedisConfig(
            url="redis://localhost:6379/0",
            enabled=False  # Use in-memory for tests
        ),
        cache=CacheConfig(
            ttl=300,
            max_size=100
        ),
        rbac=RBACConfig(
            policy_path="rbac/policy.csv",
            default_role="agent"
        ),
        server=ServerConfig(
            host="localhost",
            port=8080,
            log_level="INFO"
        ),
        otel=OTelConfig(
            enabled=False,  # Disable for tests
            exporter_otlp_endpoint="http://localhost:4317",
            service_name="okta-mcp-server-test"
        ),
        security=SecurityConfig(
            session_secret_key="test_secret_key_for_testing_only",
            token_expiry_seconds=3600
        )
    )


@pytest.fixture
async def cache_manager(test_config: Config) -> AsyncGenerator[CacheManager, None]:
    """Create cache manager for testing."""
    manager = CacheManager(test_config.redis, test_config.cache)
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.fixture
def rbac_manager() -> RBACManager:
    """Create RBAC manager for testing."""
    return RBACManager(
        model_path="rbac/model.conf",
        policy_path="rbac/policy.csv"
    )


@pytest.fixture
def session_store() -> SessionTokenStore:
    """Create session store for testing."""
    return SessionTokenStore(default_ttl=3600)


@pytest.fixture
def okta_client(test_config: Config) -> OktaClient:
    """Create Okta client for testing."""
    return OktaClient(
        config=test_config.okta,
        access_token="test_access_token"
    )
