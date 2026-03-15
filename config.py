"""
Configuration management for Okta MCP Server.

This module handles all configuration loading from environment variables
and provides a centralized configuration object.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OktaConfig(BaseSettings):
    """Okta-specific configuration."""

    domain: str = Field(..., description="Okta domain (e.g., your-domain.okta.com)")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    redirect_uri: str = Field(
        default="http://localhost:8080/callback",
        description="OAuth redirect URI"
    )
    api_token: Optional[str] = Field(
        default=None,
        description="Okta API token for service-to-service calls"
    )

    model_config = SettingsConfigDict(env_prefix="OKTA_")


class RedisConfig(BaseSettings):
    """Redis cache configuration."""

    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    enabled: bool = Field(
        default=True,
        description="Enable Redis caching"
    )

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class CacheConfig(BaseSettings):
    """Cache behavior configuration."""

    ttl: int = Field(
        default=300,
        description="Default cache TTL in seconds"
    )
    max_size: int = Field(
        default=1000,
        description="Maximum in-memory cache size"
    )

    model_config = SettingsConfigDict(env_prefix="CACHE_")


class RBACConfig(BaseSettings):
    """RBAC configuration."""

    policy_path: str = Field(
        default="rbac/policy.csv",
        description="Path to Casbin policy file"
    )
    default_role: str = Field(
        default="agent",
        description="Default role for authenticated users"
    )

    model_config = SettingsConfigDict(env_prefix="RBAC_")


class ServerConfig(BaseSettings):
    """Server configuration."""

    host: str = Field(
        default="localhost",
        description="Server host"
    )
    port: int = Field(
        default=8080,
        description="Server port"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    model_config = SettingsConfigDict(env_prefix="SERVER_")


class OTelConfig(BaseSettings):
    """OpenTelemetry configuration."""

    enabled: bool = Field(
        default=True,
        description="Enable OpenTelemetry tracing"
    )
    exporter_otlp_endpoint: str = Field(
        default="http://localhost:4317",
        description="OTLP exporter endpoint"
    )
    service_name: str = Field(
        default="okta-mcp-server",
        description="Service name for tracing"
    )

    model_config = SettingsConfigDict(env_prefix="OTEL_")


class SecurityConfig(BaseSettings):
    """Security configuration."""

    session_secret_key: str = Field(
        ...,
        description="Secret key for session encryption"
    )
    token_expiry_seconds: int = Field(
        default=3600,
        description="Access token expiry time in seconds"
    )

    model_config = SettingsConfigDict(env_prefix="")


class Config(BaseSettings):
    """Main configuration object."""

    okta: OktaConfig = Field(default_factory=OktaConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rbac: RBACConfig = Field(default_factory=RBACConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    otel: OTelConfig = Field(default_factory=OTelConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment."""
        return cls(
            okta=OktaConfig(),
            redis=RedisConfig(),
            cache=CacheConfig(),
            rbac=RBACConfig(),
            server=ServerConfig(),
            otel=OTelConfig(),
            security=SecurityConfig()
        )

    def validate_config(self) -> list[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.okta.domain:
            errors.append("OKTA_DOMAIN is required")
        if not self.okta.client_id:
            errors.append("OKTA_CLIENT_ID is required")
        if not self.okta.client_secret:
            errors.append("OKTA_CLIENT_SECRET is required")
        if not self.security.session_secret_key:
            errors.append("SESSION_SECRET_KEY is required")

        return errors


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config: The global configuration object
    """
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config() -> Config:
    """
    Reload configuration from environment.

    Returns:
        Config: The reloaded configuration object
    """
    global _config
    _config = Config.load()
    return _config
