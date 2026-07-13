"""
CaptionDB Core Exceptions.
All custom domain and infrastructure exceptions inherit from CaptionDBException.
"""
from typing import Optional, Dict, Any


class CaptionDBException(Exception):
    """
    Base exception for all domain errors.
    Requires an error code for the client and a safe message.
    """
    def __init__(
        self, 
        message: str, 
        error_code: str = "INTERNAL_ERROR", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationException(CaptionDBException):
    """Raised when business logic validation fails (e.g., video too long)."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)


class ConfigurationException(CaptionDBException):
    """Raised when application configuration is missing or invalid."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="CONFIGURATION_ERROR", details=details)


class StorageException(CaptionDBException):
    """
    Raised when a storage operation fails.
    This prevents exposing internal system errors (like OS paths) to the upper layers.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="STORAGE_ERROR", details=details)


class AIProviderException(CaptionDBException):
    """Raised when an AI provider fails to generate a response (timeouts, auth, etc.)."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="AI_PROVIDER_ERROR", details=details)


class PipelineException(CaptionDBException):
    """Raised when a pipeline stage fails unrecoverably."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="PIPELINE_ERROR", details=details)


class ExternalServiceException(CaptionDBException):
    """Raised when an external third-party API or service is unreachable."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="EXTERNAL_SERVICE_ERROR", details=details)


class NotFoundException(CaptionDBException):
    """Raised when a requested resource (e.g., video, project) does not exist."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="NOT_FOUND", details=details)


class ConflictException(CaptionDBException):
    """Raised when a request conflicts with current state (e.g., duplicate processing)."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="CONFLICT", details=details)


class MetadataExtractionError(CaptionDBException):
    """Raised when metadata extraction via FFprobe fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="METADATA_EXTRACTION_ERROR", details=details)


class SceneDetectionException(CaptionDBException):
    """Raised when Scene Detection processing fails unrecoverably."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="SCENE_DETECTION_ERROR", details=details)


# Backwards/consistency alias: the scene service raises ``SceneDetectionException``
# while the analysis pipeline (and its tests) import/catch ``SceneDetectionError``.
# Aliasing to the same class ensures the pipeline's ``except`` clause actually
# catches the error the scene service raises.
SceneDetectionError = SceneDetectionException


class FrameExtractionError(CaptionDBException):
    """Raised when frame extraction via OpenCV fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="FRAME_EXTRACTION_ERROR", details=details)


class KeyframeSelectionError(CaptionDBException):
    """Raised when keyframe analysis or selection fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="KEYFRAME_SELECTION_ERROR", details=details)


class ImagePreparationException(CaptionDBException):
    """Raised when image preprocessing fails (e.g., resizing, compression, size limits)."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="IMAGE_PREPARATION_ERROR", details=details)


class VideoAnalysisPipelineException(CaptionDBException):
    """Raised when the Video Analysis Pipeline fails completely."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="VIDEO_ANALYSIS_PIPELINE_ERROR", details=details)


class VisionAnalysisException(CaptionDBException):
    """Raised when Vision AI analysis fails to process a package or returns an invalid payload."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="VISION_ANALYSIS_ERROR", details=details)


class CaptionGenerationException(CaptionDBException):
    """Raised when the Caption Generation API fails or returns invalid payloads."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="CAPTION_GENERATION_ERROR", details=details)


# ---------------------------------------------------------------------------
# Authentication Exceptions
# ---------------------------------------------------------------------------

class AuthenticationException(CaptionDBException):
    """Raised when authentication fails (bad credentials, inactive account, etc.)."""
    def __init__(self, message: str = "Authentication failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="AUTHENTICATION_ERROR", details=details)


class InvalidCredentialsException(AuthenticationException):
    """Raised when the provided credentials are incorrect."""
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Invalid credentials.", details=details)
        self.error_code = "INVALID_CREDENTIALS"


class AccountNotActiveException(AuthenticationException):
    """Raised when a user account exists but is suspended or pending verification."""
    def __init__(self, status: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Account is not active: {status}", details=details)
        self.error_code = "ACCOUNT_NOT_ACTIVE"


class TokenExpiredException(AuthenticationException):
    """Raised when a JWT or session token has expired."""
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Token has expired.", details=details)
        self.error_code = "TOKEN_EXPIRED"


class OAuthProviderException(AuthenticationException):
    """Raised when an OAuth provider returns an error during code exchange or profile fetch."""
    def __init__(self, provider: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"OAuth provider '{provider}' error: {message}", details=details)
        self.error_code = "OAUTH_PROVIDER_ERROR"


class IdentityAlreadyLinkedException(ConflictException):
    """Raised when an OAuth identity is already linked to an account."""
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Identity is already linked to this account.", details=details)
        self.error_code = "IDENTITY_ALREADY_LINKED"


class IdentityNotFoundException(NotFoundException):
    """Raised when an identity to unlink does not exist."""
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Identity not found.", details=details)
        self.error_code = "IDENTITY_NOT_FOUND"

