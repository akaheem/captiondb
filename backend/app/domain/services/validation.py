"""
Video Validation Engine.

Resides entirely within the Domain layer. 
Contains zero dependencies on FastAPI, Storage, HTTP, or AI.
"""
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass, field

from app.domain.models.video import Video, VideoFormat


@dataclass
class ValidationResult:
    """Value object representing the outcome of a validation cycle."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)


class VideoValidator(ABC):
    """
    Abstract base class for a single-responsibility validation rule.
    """
    @abstractmethod
    def validate(self, video: Video) -> ValidationResult:
        """Executes a specific domain rule against the Video aggregate."""
        pass


class FilenameValidator(VideoValidator):
    """
    Implements rule from PROJECT_SPEC.md: 'Sanitize filenames.'
    """
    def validate(self, video: Video) -> ValidationResult:
        errors = []
        if not video.original_filename or not video.original_filename.strip():
            errors.append("Original filename cannot be empty.")
        elif ".." in video.original_filename or "/" in video.original_filename or "\\" in video.original_filename:
            errors.append("Original filename contains invalid path traversal characters.")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class PathValidator(VideoValidator):
    """
    Implements rule from PROJECT_SPEC.md: 'Normalize paths.'
    """
    def validate(self, video: Video) -> ValidationResult:
        errors = []
        if not video.logical_path or not video.logical_path.strip():
            errors.append("Logical path cannot be empty.")
        elif ".." in video.logical_path or video.logical_path.startswith("/"):
            errors.append("Logical path must be normalized and cannot contain directory traversal.")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class VideoFormatValidator(VideoValidator):
    """
    Implements validation against the domain's supported formats.
    """
    def validate(self, video: Video) -> ValidationResult:
        errors = []
        if video.metadata and video.metadata.format == VideoFormat.UNKNOWN:
            errors.append("Unsupported video format. Allowed formats are explicitly mapped in the domain.")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class ValidationService:
    """
    Domain service acting as the Validation Coordinator.
    Orchestrates independent validators and aggregates their results.
    """
    
    def __init__(self, validators: List[VideoValidator]):
        self._validators = validators

    def validate_video(self, video: Video) -> ValidationResult:
        """Runs the video through all registered validation rules."""
        all_errors = []
        
        for validator in self._validators:
            result = validator.validate(video)
            if not result.is_valid:
                all_errors.extend(result.errors)
                
        return ValidationResult(is_valid=len(all_errors) == 0, errors=all_errors)
