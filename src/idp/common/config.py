"""Centralized configuration management using pydantic-settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MinIOConfig(BaseSettings):
    """MinIO (Bronze Layer) configuration."""

    endpoint: str = Field(default="localhost:9000")
    access_key: str = Field(default="minioadmin")
    secret_key: str = Field(default="minioadmin")
    secure: bool = Field(default=False)
    bucket_bronze: str = Field(default="bronze")

    model_config = SettingsConfigDict(env_prefix="MINIO_")


class PostgresConfig(BaseSettings):
    """PostgreSQL (Gold Layer) configuration."""

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    db: str = Field(default="idp")
    user: str = Field(default="idp_user")
    password: str = Field(default="changeme")

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class DuckDBConfig(BaseSettings):
    """DuckDB (Transformation Layer) configuration."""

    path: str = Field(default="data/gold.duckdb")

    model_config = SettingsConfigDict(env_prefix="DUCKDB_")


class GeminiConfig(BaseSettings):
    """Gemini API configuration."""

    api_key: str | None = Field(default=None)
    embedding_model: str = Field(default="text-embedding-004")
    chat_model: str = Field(default="gemini-2.0-flash")

    model_config = SettingsConfigDict(env_prefix="GEMINI_")


class APIConfig(BaseSettings):
    """FastAPI server configuration."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(env_prefix="API_")


class ProxyConfig(BaseSettings):
    """Proxy configuration for external requests."""

    http_proxy: str | None = Field(default=None)
    https_proxy: str | None = Field(default=None)
    no_proxy: str = Field(default="localhost,127.0.0.1")

    model_config = SettingsConfigDict(env_prefix="")

    def get_proxies(self) -> dict[str, str] | None:
        """Get proxy dict for httpx/requests."""
        if self.http_proxy or self.https_proxy:
            return {
                "http://": self.http_proxy or "",
                "https://": self.https_proxy or "",
            }
        return None


class Settings(BaseSettings):
    """Application-wide settings."""

    minio: MinIOConfig = Field(default_factory=MinIOConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    duckdb: DuckDBConfig = Field(default_factory=DuckDBConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
