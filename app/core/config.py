"""Configuration management for the Order Management Service"""

from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    app_name: str = "Order Management Service"
    app_version: str = "1.0.0"
    debug: bool = False

    # API settings
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: list[str] = ["*"]

    # Database settings (Azure Cosmos DB)
    cosmos_endpoint: Optional[str] = None
    cosmos_key: Optional[str] = None
    cosmos_database: str = "OrderManagement"
    cosmos_container: str = "Orders"

    # For local development - use Cosmos DB Emulator
    cosmos_emulator_endpoint: str = "https://localhost:8081"
    cosmos_emulator_key: str = (
        "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
    )

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def use_cosmos_emulator(self) -> bool:
        """Check if we should use the Cosmos DB emulator."""
        return self.cosmos_endpoint is None

    @property
    def effective_cosmos_endpoint(self) -> str:
        """Get the effective Cosmos DB endpoint."""
        return self.cosmos_endpoint or self.cosmos_emulator_endpoint

    @property
    def effective_cosmos_key(self) -> str:
        """Get the effective Cosmos DB key."""
        return self.cosmos_key or self.cosmos_emulator_key


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
