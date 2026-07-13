"""
Infrastructure Dependencies.
Registers providers for external systems (Storage, AI, Cache, Database).
"""
from typing import Generator, Any
from fastapi import Depends

from typing import AsyncGenerator

from app.core.config import Settings, get_settings
from app.infrastructure.database.engine import create_db_engine
from app.infrastructure.database.session import get_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

# Singletons for Database
_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker | None = None

def get_engine(settings: Settings = Depends(get_settings)) -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_db_engine(settings.database)
    return _engine

def get_db_sessionmaker(engine: AsyncEngine = Depends(get_engine)) -> async_sessionmaker:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = get_sessionmaker(engine)
    return _sessionmaker

async def get_async_session(session_maker: async_sessionmaker = Depends(get_db_sessionmaker)) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a localized SQLAlchemy AsyncSession per request.
    Yields the session and safely rolls back/closes it upon completion or failure.
    """
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

from app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from app.infrastructure.database.uow.unit_of_work import SQLAlchemyUnitOfWork

def get_unit_of_work(session_maker: async_sessionmaker = Depends(get_db_sessionmaker)) -> AbstractUnitOfWork:
    """
    Dependency providing the centralized Unit of Work.
    Services should request this rather than raw repositories.
    """
    return SQLAlchemyUnitOfWork(session_maker)

# Domain Interfaces
from app.domain.interfaces.storage import StorageProvider
from app.domain.interfaces.ai import AIProvider
from app.domain.interfaces.cache import CacheProvider
from app.domain.interfaces.metadata import MetadataExtractor

# ---------------------------------------------------------------------------
# Storage Providers
# ---------------------------------------------------------------------------
def get_storage_provider(settings: Settings = Depends(get_settings)) -> StorageProvider:
    """
    Dependency provider for the Storage layer.
    
    Currently returns the LocalStorageAdapter if configured, or raises NotImplementedError.
    During unit tests, this can be overridden using:
    app.dependency_overrides[get_storage_provider] = lambda: MockStorageProvider()
    """
    if settings.storage.provider == "local":
        # We import here to avoid circular dependencies if infrastructure modules import config
        from app.infrastructure.storage.local import LocalStorageAdapter
        return LocalStorageAdapter(base_path=settings.storage.local_storage_path)
    
    raise NotImplementedError(f"Storage provider '{settings.storage.provider}' is not yet implemented.")


# ---------------------------------------------------------------------------
# AI Providers
# ---------------------------------------------------------------------------
def get_ai_provider(settings: Settings = Depends(get_settings)) -> AIProvider:
    """
    Dependency placeholder for the AI layer.
    
    Will eventually instantiate the FireworksClient or other AI providers based on settings.
    """
    raise NotImplementedError("AIProvider implementation is not yet complete.")


# ---------------------------------------------------------------------------
# Cache Providers
# ---------------------------------------------------------------------------
def get_cache_provider(settings: Settings = Depends(get_settings)) -> CacheProvider:
    """
    Dependency placeholder for the Caching layer (Redis/Memory).
    """
    raise NotImplementedError("CacheProvider implementation is not yet complete.")


# ---------------------------------------------------------------------------
# Database Providers
# ---------------------------------------------------------------------------
def get_db_session() -> Generator[Any, None, None]:
    """
    Dependency placeholder for Database sessions (e.g., SQLAlchemy session).
    """
    raise NotImplementedError("Database is not yet implemented.")


# ---------------------------------------------------------------------------
# Metadata Extractors
# ---------------------------------------------------------------------------
def get_metadata_extractor(settings: Settings = Depends(get_settings)) -> "FFprobeMetadataExtractor":
    """Provides the concrete FFprobe extractor."""
    from app.infrastructure.metadata.ffprobe import FFprobeMetadataExtractor
    return FFprobeMetadataExtractor(timeout_seconds=settings.METADATA_TIMEOUT_SECONDS)


def get_scene_detector() -> "PySceneDetectDetector":
    """Provides the concrete PySceneDetect adapter."""
    from app.infrastructure.scene.pyscenedetect import PySceneDetectDetector
    return PySceneDetectDetector()


# ---------------------------------------------------------------------------
# Frame Extractors
# ---------------------------------------------------------------------------
def get_frame_extractor() -> "OpenCVFrameExtractor":
    """Provides the concrete OpenCV frame extractor."""
    from app.infrastructure.frame.opencv_extractor import OpenCVFrameExtractor
    return OpenCVFrameExtractor()


# ---------------------------------------------------------------------------
# Keyframe Quality & Selection
# ---------------------------------------------------------------------------
def get_frame_quality_analyzer() -> "OpenCVFrameQualityAnalyzer":
    """Provides the OpenCV implementation for frame analysis."""
    from app.infrastructure.keyframe.opencv import OpenCVFrameQualityAnalyzer
    return OpenCVFrameQualityAnalyzer()


def get_keyframe_selector(
    analyzer = Depends(get_frame_quality_analyzer)
) -> "OpenCVKeyframeSelector":
    """Provides the OpenCV keyframe selector."""
    from app.infrastructure.keyframe.opencv import OpenCVKeyframeSelector
    return OpenCVKeyframeSelector(analyzer=analyzer)


# ---------------------------------------------------------------------------
# Vision Input Preparation
# ---------------------------------------------------------------------------
def get_image_preprocessor() -> "ImagePreprocessor":
    """
    Provides the image preprocessor.
    Currently a stub as OpenCVImagePreprocessor is deferred to a future phase.
    """
    raise NotImplementedError("OpenCVImagePreprocessor is not yet implemented.")


# ---------------------------------------------------------------------------
# Vision Analysis Subsystem
# ---------------------------------------------------------------------------
def get_vision_analyzer() -> "VisionAnalyzer":
    """
    Provides the VisionAnalyzer implementation.
    Currently a stub as FireworksVisionAdapter is deferred to a future phase.
    """
    raise NotImplementedError("FireworksVisionAdapter is not yet implemented.")


# ---------------------------------------------------------------------------
# Caption Generation Subsystem
# ---------------------------------------------------------------------------
def get_caption_generator(settings: Settings = Depends(get_settings)) -> "CaptionGenerator":
    """
    Provides the CaptionGenerator implementation.
    Instantiates the FireworksCaptionAdapter using AIProviderSettings.
    """
    from app.infrastructure.caption.fireworks_adapter import FireworksCaptionAdapter
    
    if settings.ai.provider == "fireworks":
        return FireworksCaptionAdapter(settings=settings.ai)
        
    raise NotImplementedError(f"Caption generator for provider '{settings.ai.provider}' is not implemented.")


# ---------------------------------------------------------------------------
# Authentication & Identity Subsystem
# ---------------------------------------------------------------------------
from app.domain.interfaces.auth import (
    AuthenticationProvider,
    UserProvider,
    SessionProvider,
    TokenProvider,
    PasswordHasher,
    PasswordPolicyProvider,
    PasswordCredentialProvider,
    IdentityProvider as ExternalIdentityProvider,
)
from app.domain.models.auth import OAuthProvider


def get_auth_provider() -> AuthenticationProvider:
    """Dependency placeholder for AuthenticationProvider."""
    raise NotImplementedError("AuthenticationProvider is not yet implemented.")

def get_user_provider() -> UserProvider:
    """Dependency placeholder for UserProvider."""
    raise NotImplementedError("UserProvider is not yet implemented.")


def get_session_provider() -> SessionProvider:
    """Dependency placeholder for SessionProvider."""
    raise NotImplementedError("SessionProvider is not yet implemented.")


def get_token_provider() -> TokenProvider:
    """Dependency placeholder for TokenProvider."""
    raise NotImplementedError("TokenProvider is not yet implemented.")


def get_password_hasher() -> PasswordHasher:
    """Dependency placeholder for PasswordHasher."""
    raise NotImplementedError("PasswordHasher is not yet implemented.")

def get_password_policy_provider() -> PasswordPolicyProvider:
    """Dependency placeholder for PasswordPolicyProvider."""
    raise NotImplementedError("PasswordPolicyProvider is not yet implemented.")

def get_password_credential_provider() -> PasswordCredentialProvider:
    """Dependency placeholder for PasswordCredentialProvider."""
    raise NotImplementedError("PasswordCredentialProvider is not yet implemented.")

def get_external_identity_providers() -> dict[OAuthProvider, ExternalIdentityProvider]:
    """Dependency placeholder for External Identity Providers (Google, GitHub, etc)."""
    raise NotImplementedError("External Identity Providers are not yet implemented.")

from app.services.oauth_registry import OAuthProviderRegistry
from app.domain.models.auth import OAuthProvider as OAuthProviderEnum

# Module-level singleton — shared client pools across requests.
_oauth_registry: OAuthProviderRegistry | None = None

def get_oauth_provider_registry(settings: Settings = Depends(get_settings)) -> OAuthProviderRegistry:
    """
    Builds (once) and returns the OAuthProviderRegistry populated with every
    provider whose credentials are configured in Settings.

    Adding a new provider requires only:
      1. Create a new adapter class.
      2. Add its config block to OAuthSettings.
      3. Register it here.

    No application or service code needs to change.
    """
    global _oauth_registry
    if _oauth_registry is not None:
        return _oauth_registry

    from app.infrastructure.auth.oauth import (
        GoogleOAuthAdapter,
        GitHubOAuthAdapter,
        AppleOAuthAdapter,
        MicrosoftOAuthAdapter,
        TwitterOAuthAdapter,
    )
    timeout = settings.oauth.http_timeout_seconds
    registry = OAuthProviderRegistry()

    if settings.oauth.google.client_id:
        registry.register_provider(OAuthProviderEnum.GOOGLE, GoogleOAuthAdapter(settings.oauth.google, timeout))

    if settings.oauth.github.client_id:
        registry.register_provider(OAuthProviderEnum.GITHUB, GitHubOAuthAdapter(settings.oauth.github, timeout))

    if settings.oauth.apple.client_id:
        registry.register_provider(OAuthProviderEnum.APPLE, AppleOAuthAdapter(settings.oauth.apple, timeout))

    if settings.oauth.microsoft.client_id:
        registry.register_provider(OAuthProviderEnum.MICROSOFT, MicrosoftOAuthAdapter(settings.oauth.microsoft, timeout))

    if settings.oauth.twitter.client_id:
        registry.register_provider(OAuthProviderEnum.TWITTER, TwitterOAuthAdapter(settings.oauth.twitter, timeout))

    _oauth_registry = registry
    return _oauth_registry
