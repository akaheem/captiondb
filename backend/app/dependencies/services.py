from fastapi import Depends

from app.core.config import Settings, get_settings

from app.domain.interfaces.storage import StorageProvider
from app.domain.interfaces.ai import AIProvider
from app.domain.interfaces.cache import CacheProvider
from app.domain.interfaces.metadata import MetadataExtractor

from app.services.storage import StorageService
from app.services.ai import AIService
from app.services.cache import CacheService
from app.services.file import FileManagementService
from app.domain.interfaces.task_dispatcher import AbstractTaskDispatcher
from app.services.metadata import MetadataExtractionService
from app.services.scene import SceneDetectionService

from .infrastructure import (
    get_storage_provider, 
    get_ai_provider, 
    get_cache_provider,
    get_metadata_extractor,
    get_scene_detector,
    get_frame_extractor,
    get_keyframe_selector,
    get_image_preprocessor,
    get_vision_analyzer,
    get_caption_generator,
    get_unit_of_work,
    get_user_provider,
    get_session_provider,
    get_token_provider,
    get_password_hasher,
    get_auth_provider,
    get_external_identity_providers,
    get_password_policy_provider,
    get_password_credential_provider,
    get_oauth_provider_registry
)


# ===========================================================================
# Domain / Application Services
# ===========================================================================

def get_storage_service(
    provider: StorageProvider = Depends(get_storage_provider)
) -> StorageService:
    return StorageService(provider=provider)


def get_ai_service(
    provider: AIProvider = Depends(get_ai_provider)
) -> AIService:
    return AIService(provider=provider)


def get_cache_service(
    provider: CacheProvider = Depends(get_cache_provider)
) -> CacheService:
    return CacheService(provider=provider)


def get_file_management_service(
    storage_service: StorageService = Depends(get_storage_service),
    settings: Settings = Depends(get_settings)
) -> FileManagementService:
    """
    Dependency provider for FileManagementService.
    FastAPI resolves the lower-level StorageService and injects it.
    """
    return FileManagementService(storage_service=storage_service, settings=settings)


# ===========================================================================
# Domain Services (Pure Business Logic)
# ===========================================================================

def get_validation_service() -> "ValidationService":
    """
    Dependency provider for the Video Validation Engine.
    Instantiates the service with the explicitly defined domain validators.
    """
    # Import locally to avoid circular dependencies if needed
    from app.domain.services.validation import (
        ValidationService, 
        FilenameValidator, 
        PathValidator, 
        VideoFormatValidator
    )
    
    validators = [
        FilenameValidator(),
        PathValidator(),
        VideoFormatValidator()
    ]
    return ValidationService(validators=validators)


def get_metadata_extraction_service(
    extractor: MetadataExtractor = Depends(get_metadata_extractor),
    settings: Settings = Depends(get_settings)
) -> "MetadataExtractionService":
    """
    Dependency provider for MetadataExtractionService.
    FastAPI resolves the abstract MetadataExtractor (e.g. FFprobeAdapter) and securely injects it.

    Defined before ``get_upload_service`` because it is referenced as a
    ``Depends(...)`` default there, and default arguments are evaluated at
    function-definition time.
    """
    from app.services.metadata import MetadataExtractionService
    return MetadataExtractionService(extractor=extractor, settings=settings)


def get_upload_service(
    validation_service: "ValidationService" = Depends(get_validation_service),
    file_management_service: FileManagementService = Depends(get_file_management_service),
    storage_service: StorageService = Depends(get_storage_service),
    metadata_service: "MetadataExtractionService" = Depends(get_metadata_extraction_service),
    settings: Settings = Depends(get_settings),
    unit_of_work=Depends(get_unit_of_work)
) -> "UploadService":
    """
    Dependency provider for UploadService.
    Instantiates the upload coordinator with its required application and domain services.
    """
    from app.services.upload import UploadService
    return UploadService(
        validation_service=validation_service,
        file_management_service=file_management_service,
        storage_service=storage_service,
        metadata_service=metadata_service,
        settings=settings,
        unit_of_work=unit_of_work
    )


def get_scene_detection_service(
    scene_detector=Depends(get_scene_detector),
    storage_service: StorageService = Depends(get_storage_service)
) -> "SceneDetectionService":
    """
    Dependency provider for SceneDetectionService.
    """
    from app.services.scene import SceneDetectionService
    return SceneDetectionService(scene_detector=scene_detector, storage_service=storage_service)


def get_frame_sampling_service(
    frame_extractor=Depends(get_frame_extractor),
    storage_service: StorageService = Depends(get_storage_service)
) -> "FrameSamplingService":
    """
    Dependency provider for FrameSamplingService.
    """
    from app.services.frame import FrameSamplingService
    return FrameSamplingService(frame_extractor=frame_extractor, storage_service=storage_service)


def get_keyframe_selection_service(
    keyframe_selector=Depends(get_keyframe_selector)
) -> "KeyframeSelectionService":
    """
    Dependency provider for KeyframeSelectionService.
    """
    from app.services.keyframe import KeyframeSelectionService
    return KeyframeSelectionService(keyframe_selector=keyframe_selector)


def get_vision_preparation_service(
    image_preprocessor=Depends(get_image_preprocessor)
) -> "VisionInputPreparationService":
    """
    Dependency provider for VisionInputPreparationService.
    """
    from app.services.vision_preparation import VisionInputPreparationService
    return VisionInputPreparationService(image_preprocessor=image_preprocessor)


def get_video_analysis_pipeline(
    scene_service=Depends(get_scene_detection_service),
    frame_service=Depends(get_frame_sampling_service),
    keyframe_service=Depends(get_keyframe_selection_service),
    vision_prep_service=Depends(get_vision_preparation_service)
) -> "VideoAnalysisPipeline":
    """
    Dependency provider for the complete Video Analysis Pipeline.
    """
    from app.services.video_analysis_pipeline import VideoAnalysisPipeline
    return VideoAnalysisPipeline(
        scene_service=scene_service,
        frame_service=frame_service,
        keyframe_service=keyframe_service,
        vision_prep_service=vision_prep_service
    )


def get_prompt_builder() -> "PromptBuilder":
    """
    Dependency provider for PromptBuilder.
    """
    from app.services.prompt_builder import PromptBuilder
    return PromptBuilder()


def get_vision_analysis_service(
    analyzer=Depends(get_vision_analyzer),
    prompt_builder=Depends(get_prompt_builder)
) -> "VisionAnalysisService":
    """
    Dependency provider for VisionAnalysisService.
    """
    from app.services.vision import VisionAnalysisService
    return VisionAnalysisService(analyzer=analyzer, prompt_builder=prompt_builder)


def get_caption_generation_service(
    generator=Depends(get_caption_generator),
    prompt_builder=Depends(get_prompt_builder)
) -> "CaptionGenerationService":
    """
    Dependency provider for CaptionGenerationService.
    """
    from app.services.caption_generation import CaptionGenerationService
    return CaptionGenerationService(generator=generator, prompt_builder=prompt_builder)


def get_scene_result_integration_service() -> "SceneResultIntegrationService":
    """
    Dependency provider for SceneResultIntegrationService.

    Defined before ``get_ai_pipeline_service`` because it is referenced as a
    ``Depends(...)`` default there, and default arguments are evaluated at
    function-definition time.
    """
    from app.services.scene_result_integration import SceneResultIntegrationService
    return SceneResultIntegrationService()


def get_ai_pipeline_service(
    video_pipeline=Depends(get_video_analysis_pipeline),
    vision_service=Depends(get_vision_analysis_service),
    caption_service=Depends(get_caption_generation_service),
    scene_integration_service=Depends(get_scene_result_integration_service),
    unit_of_work=Depends(get_unit_of_work)
) -> "AIPipelineService":
    """
    Dependency provider for AIPipelineService.
    """
    from app.services.ai_pipeline import AIPipelineService
    return AIPipelineService(
        video_pipeline=video_pipeline,
        vision_service=vision_service,
        caption_service=caption_service,
        scene_integration_service=scene_integration_service,
        unit_of_work=unit_of_work
    )


def get_project_service(
    unit_of_work=Depends(get_unit_of_work),
    file_service=Depends(get_file_management_service)
) -> "ProjectService":
    """
    Dependency provider for ProjectService.
    """
    from app.services.project import ProjectService
    return ProjectService(unit_of_work=unit_of_work, file_service=file_service)

def get_task_dispatcher() -> AbstractTaskDispatcher:
    """
    Dependency provider for AbstractTaskDispatcher.
    Provides the Celery implementation.
    """
    from app.infrastructure.tasks.celery_dispatcher import CeleryTaskDispatcher
    return CeleryTaskDispatcher()

def get_background_task_service(
    dispatcher: AbstractTaskDispatcher = Depends(get_task_dispatcher)
) -> "BackgroundTaskService":
    """
    Dependency provider for BackgroundTaskService.
    """
    from app.services.task import BackgroundTaskService
    return BackgroundTaskService(dispatcher=dispatcher)

def get_task_monitor(cache_service = Depends(get_cache_service)) -> "AbstractTaskMonitor":
    """
    Dependency provider for AbstractTaskMonitor.
    Uses the CacheTaskMonitor implementation by default.
    """
    from app.infrastructure.monitoring.cache_monitor import CacheTaskMonitor
    return CacheTaskMonitor(cache_service=cache_service)

def get_task_monitoring_service(monitor = Depends(get_task_monitor)) -> "TaskMonitoringService":
    """
    Dependency provider for TaskMonitoringService.
    """
    from app.services.task_monitoring import TaskMonitoringService
    return TaskMonitoringService(monitor=monitor)

# ---------------------------------------------------------------------------
# Authentication & Identity Subsystem
# ---------------------------------------------------------------------------
def get_authentication_service(
    auth_provider=Depends(get_auth_provider),
    user_provider=Depends(get_user_provider),
    identity_provider=Depends(get_external_identity_providers),
) -> "AuthenticationService":
    """
    Dependency provider for AuthenticationService.
    """
    from app.services.auth import AuthenticationService
    # identity_provider here would ideally be a single IdentityProvider or a factory/dict.
    # We will pass the dictionary of providers for now or a singular one if we abstract it.
    # The interface in app.services.auth expects IdentityProvider. We'll cast/pass it.
    return AuthenticationService(
        auth_provider=auth_provider,
        user_provider=user_provider,
        identity_provider=identity_provider,
    )

def get_token_service(
    token_provider=Depends(get_token_provider)
) -> "TokenService":
    from app.services.token import TokenService
    return TokenService(token_provider=token_provider)

def get_session_service(
    session_provider=Depends(get_session_provider)
) -> "SessionService":
    from app.services.session import SessionService
    return SessionService(session_provider=session_provider)

def get_email_authentication_service(
    user_provider=Depends(get_user_provider),
    password_hasher=Depends(get_password_hasher),
    password_policy_provider=Depends(get_password_policy_provider),
    credential_provider=Depends(get_password_credential_provider)
) -> "EmailAuthenticationService":
    from app.services.email_auth import EmailAuthenticationService
    return EmailAuthenticationService(
        user_provider=user_provider,
        password_hasher=password_hasher,
        password_policy_provider=password_policy_provider,
        credential_provider=credential_provider
    )

def get_oauth_authentication_service(
    registry=Depends(get_oauth_provider_registry),
    auth_service=Depends(get_authentication_service),
    user_provider=Depends(get_user_provider)
) -> "OAuthAuthenticationService":
    from app.services.oauth_auth import OAuthAuthenticationService
    return OAuthAuthenticationService(
        registry=registry,
        auth_service=auth_service,
        user_provider=user_provider
    )

# ---------------------------------------------------------------------------
# Authorization & Request Context (Phase 9.8)
# ---------------------------------------------------------------------------

def get_authorization_service(
    token_service=Depends(get_token_service),
    user_provider=Depends(get_user_provider),
    session_service=Depends(get_session_service),
) -> "AuthorizationService":
    """
    Dependency provider for AuthorizationService.

    Used at startup to create the AuthenticationMiddleware instance.
    Can also be injected directly in tests.
    """
    from app.services.authorization import AuthorizationService
    return AuthorizationService(
        token_service=token_service,
        user_provider=user_provider,
        session_service=session_service,
    )


def get_request_context(request: "Request") -> "RequestContext":
    """
    FastAPI dependency that reads the RequestContext attached by
    AuthenticationMiddleware.

    Returns an anonymous context when no token was provided.
    Never raises — callers decide whether authentication is required.
    """
    from fastapi import Request
    from app.domain.models.request_context import RequestContext
    ctx = getattr(request.state, "auth_context", None)
    if ctx is None:
        return RequestContext.anonymous()
    return ctx


def get_current_user(
    request: "Request",
    context: "RequestContext" = Depends(get_request_context),
) -> "User":
    """
    FastAPI dependency that returns the authenticated domain User.

    Raises HTTP 401 when:
      - No valid token was supplied.
      - The token was expired or invalid.
      - The account is not active.

    Inject this into any endpoint that requires authentication.
    """
    from fastapi import Request, HTTPException, status
    from app.domain.models.request_context import RequestContext

    if not context.is_authenticated or context.user is None:
        # Surface the specific error code captured by the middleware
        auth_error = getattr(request.state, "auth_error", "AUTHENTICATION_ERROR")
        error_messages = {
            "TOKEN_EXPIRED":      "Access token has expired.",
            "ACCOUNT_NOT_ACTIVE": "Account is not active or not verified.",
            "INTERNAL_ERROR":     "An internal error occurred during authentication.",
        }
        msg = error_messages.get(auth_error, "Authentication required.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": auth_error, "message": msg},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return context.user

def get_authentication_api_service(
    auth_service=Depends(get_authentication_service),
    email_auth_service=Depends(get_email_authentication_service),
    oauth_auth_service=Depends(get_oauth_authentication_service),
    token_service=Depends(get_token_service),
    session_service=Depends(get_session_service),
) -> "AuthenticationApiService":
    """
    Dependency provider for AuthenticationApiService.

    This is the ONLY service that FastAPI routers should ever inject for
    authentication operations.  All sub-services are resolved here and
    must never be imported directly in router modules.
    """
    from app.api.v1.auth.service import AuthenticationApiService
    return AuthenticationApiService(
        auth_service=auth_service,
        email_auth_service=email_auth_service,
        oauth_auth_service=oauth_auth_service,
        token_service=token_service,
        session_service=session_service,
    )


# ---------------------------------------------------------------------------
# Session Management & OAuth Identity (Phase 9.9)
# ---------------------------------------------------------------------------

def get_session_management_service(
    session_provider=Depends(get_session_provider),
) -> "SessionManagementService":
    """
    Dependency provider for SessionManagementService.

    Inject this into any router that manages user sessions (list, revoke, etc.).
    Never inject SessionService or SessionProvider directly into routers.
    """
    from app.services.session_management import SessionManagementService
    return SessionManagementService(session_provider=session_provider)


def get_oauth_identity_service(
    auth_service=Depends(get_authentication_service),
    oauth_auth_service=Depends(get_oauth_authentication_service),
) -> "OAuthIdentityService":
    """
    Dependency provider for OAuthIdentityService.

    Inject this into any router that manages OAuth identity linking/unlinking.
    """
    from app.services.oauth_identity import OAuthIdentityService
    return OAuthIdentityService(
        auth_service=auth_service,
        oauth_auth_service=oauth_auth_service,
    )
