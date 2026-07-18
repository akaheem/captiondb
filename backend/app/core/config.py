"""
Core configuration system for CaptionDB.
Implements a strongly typed, environment-driven configuration hierarchy.
"""
from functools import lru_cache
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseModel):
    """Application metadata and environment settings."""
    name: str = "CaptionDB"
    version: str = "0.1.0"
    environment: Literal["development", "testing", "staging", "production"] = "development"


class APISettings(BaseModel):
    """API routing and server configuration."""
    v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000


class LoggingSettings(BaseModel):
    """Logging behavior and formatting."""
    level: str = "INFO"
    format: str = "json"


class SecuritySettings(BaseModel):
    """Security, tokens, and cryptographic keys."""
    # In a real environment, this MUST be overridden.
    secret_key: str = Field(default="CHANGE_ME_IN_PRODUCTION")
    access_token_expire_minutes: int = 60


class CORSSettings(BaseModel):
    """Cross-Origin Resource Sharing settings."""
    allowed_origins: List[str] = ["*"]
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]


class StorageSettings(BaseSettings):
    """Storage-specific settings."""
    model_config = SettingsConfigDict(env_prefix="STORAGE__")
    
    provider: Literal["local", "gcs", "s3"] = "local"
    local_storage_path: str = "./data/storage"


class DatabaseSettings(BaseSettings):
    """Database connection and pooling settings."""
    model_config = SettingsConfigDict(env_prefix="DATABASE__")

    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: str = "postgres"
    database: str = "captiondb"

    pool_size: int = 20
    max_overflow: int = 10
    echo: bool = False

    # SSL mode passed to asyncpg: disable | allow | prefer | require | verify-ca | verify-full
    # "prefer" tries SSL first and falls back to plaintext, so it works both
    # locally (no SSL) and on managed Postgres (SSL required).
    ssl_mode: str = "prefer"

    @property
    def async_database_url(self) -> str:
        """Constructs the async SQLAlchemy connection string."""
        return (
            f"postgresql+asyncpg://"
            f"{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?ssl={self.ssl_mode}"
        )


class AIProviderSettings(BaseModel):
    """AI Provider configurations (credentials and routing)."""
    provider: Literal["fireworks", "openai", "gemini"] = "fireworks"
    api_key: Optional[str] = None
    default_model: str = "accounts/fireworks/models/llama4-maverick-instruct-basic"
    max_retries: int = 3
    timeout_seconds: int = 30


class ProcessingSettings(BaseModel):
    """Video processing limits and parameters."""
    max_video_size_mb: int = 500
    max_duration_seconds: int = 3600
    default_frame_sample_rate: int = 1


class FeatureFlags(BaseModel):
    """Toggles for optional or experimental features."""
    enable_ocr: bool = False
    enable_memory: bool = False
    enable_judge: bool = False


class BackgroundTaskSettings(BaseSettings):
    """Background task and Celery settings."""
    model_config = SettingsConfigDict(env_prefix="TASKS__")
    
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"


class OAuthProviderConfig(BaseModel):
    """
    Per-provider OAuth configuration.
    All URLs are driven from config — adapters MUST NOT hardcode endpoints.
    """
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    authorization_endpoint: str = ""
    token_endpoint: str = ""
    userinfo_endpoint: str = ""
    scopes: List[str] = []
    # Apple-specific fields
    team_id: Optional[str] = None
    key_id: Optional[str] = None
    private_key_pem: Optional[str] = None
    # Twitter-specific OAuth 2.0 PKCE fields
    pkce_enabled: bool = False


class AdminSettings(BaseSettings):
    """
    Admin console credentials, loaded from environment.
    ADMIN__EMAIL — the sole administrator account email.
    ADMIN__PASSWORD_HASH — PBKDF2 hash: pbkdf2_sha256$<iters>$<salt_hex>$<hash_hex>
    """
    model_config = SettingsConfigDict(env_prefix="ADMIN__")

    email: str = ""
    password_hash: str = ""
    token_expire_minutes: int = 720  # 12 hours


class OAuthSettings(BaseSettings):
    """OAuth provider credentials and endpoints loaded from environment."""
    model_config = SettingsConfigDict(env_prefix="OAUTH__")

    google: OAuthProviderConfig = OAuthProviderConfig(
        authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        userinfo_endpoint="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=["openid", "email", "profile"],
    )
    github: OAuthProviderConfig = OAuthProviderConfig(
        authorization_endpoint="https://github.com/login/oauth/authorize",
        token_endpoint="https://github.com/login/oauth/access_token",
        userinfo_endpoint="https://api.github.com/user",
        scopes=["read:user", "user:email"],
    )
    apple: OAuthProviderConfig = OAuthProviderConfig(
        authorization_endpoint="https://appleid.apple.com/auth/authorize",
        token_endpoint="https://appleid.apple.com/auth/token",
        userinfo_endpoint="",  # Apple does not have a separate userinfo endpoint
        scopes=["openid", "email", "name"],
    )
    microsoft: OAuthProviderConfig = OAuthProviderConfig(
        authorization_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        userinfo_endpoint="https://graph.microsoft.com/v1.0/me",
        scopes=["openid", "email", "profile", "User.Read"],
    )
    twitter: OAuthProviderConfig = OAuthProviderConfig(
        authorization_endpoint="https://twitter.com/i/oauth2/authorize",
        token_endpoint="https://api.twitter.com/2/oauth2/token",
        userinfo_endpoint="https://api.twitter.com/2/users/me",
        scopes=["tweet.read", "users.read", "offline.access"],
        pkce_enabled=True,
    )

    # Request timeout / retry knobs shared by all adapters
    http_timeout_seconds: int = 10
    http_max_retries: int = 3


class Settings(BaseSettings):
    """
    Root configuration object.
    Loads values from environment variables or .env file.
    Uses '__' (double underscore) to map environment variables to nested models.
    Example: APP__ENVIRONMENT=production overrides app.environment
    """
    app: AppSettings = AppSettings()
    api: APISettings = APISettings()
    environment: str = Field("development", validation_alias="APP__ENVIRONMENT")
    debug: bool = Field(False, validation_alias="APP__DEBUG")
    
    # Nested Configuration Objects
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    ai: AIProviderSettings = Field(default_factory=AIProviderSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    processing: ProcessingSettings = ProcessingSettings()
    features: FeatureFlags = FeatureFlags()
    tasks: BackgroundTaskSettings = Field(default_factory=BackgroundTaskSettings)
    oauth: OAuthSettings = Field(default_factory=OAuthSettings)
    admin: AdminSettings = Field(default_factory=AdminSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings object.
    This guarantees immutable configuration during a request lifecycle
    and prevents repetitive disk I/O for .env loading.
    """
    return Settings()
