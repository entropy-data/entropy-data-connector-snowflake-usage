"""Configuration management for Entropy Data Connector."""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class EntropyConfig:
    """Configuration for Entropy Data API."""

    host: str = field(default_factory=lambda: os.getenv("ENTROPY_HOST", "https://api.entropy-data.com"))
    api_key: str = field(default_factory=lambda: os.getenv("ENTROPY_API_KEY", ""))

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("ENTROPY_API_KEY is required")


@dataclass
class SnowflakeConfig:
    """Configuration for Snowflake connection."""

    user: str = field(default_factory=lambda: os.getenv("SNOWFLAKE_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("SNOWFLAKE_PASSWORD", ""))
    role: str = field(default_factory=lambda: os.getenv("SNOWFLAKE_ROLE", ""))
    warehouse: Optional[str] = field(default_factory=lambda: os.getenv("SNOWFLAKE_WAREHOUSE"))

    def __post_init__(self):
        if not self.user:
            raise ValueError("SNOWFLAKE_USER is required")
        if not self.password:
            raise ValueError("SNOWFLAKE_PASSWORD is required")


@dataclass
class FilterConfig:
    """Configuration for filtering query history."""

    exclude_users: list[str] = field(default_factory=lambda: _parse_list(os.getenv("EXCLUDE_USERS", "")))
    exclude_roles: list[str] = field(default_factory=lambda: _parse_list(os.getenv("EXCLUDE_ROLES", "")))
    exclude_warehouses: list[str] = field(default_factory=lambda: _parse_list(os.getenv("EXCLUDE_WAREHOUSES", "")))
    days_back: int = field(default_factory=lambda: int(os.getenv("QUERY_DAYS_BACK", "30")))


@dataclass
class Config:
    """Main configuration object."""

    entropy: EntropyConfig = field(default_factory=EntropyConfig)
    snowflake: SnowflakeConfig = field(default_factory=SnowflakeConfig)
    filters: FilterConfig = field(default_factory=FilterConfig)


def _parse_list(value: str) -> list[str]:
    """Parse comma-separated string into list."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
