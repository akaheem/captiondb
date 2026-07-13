"""
Scene Detection Engine.
Application service that orchestrates scene boundary identification and validation.
"""
from typing import List
from loguru import logger

from app.domain.interfaces.scene import SceneDetector
from app.domain.models.video import Scene
from app.domain.models.analysis import ProcessingContext
from app.services.storage import StorageService
from app.core.exceptions import ValidationException, MetadataExtractionError, SceneDetectionException


class SceneDetectionService:
    """
    Coordinates the execution of video scene detection.
    Responsible for validating boundaries, handling failures, 
    and integrating with the Video Analysis Subsystem context.
    """
    
    def __init__(self, scene_detector: SceneDetector, storage_service: StorageService):
        """Injected dependencies."""
        self._detector = scene_detector
        self._storage = storage_service

    async def process(self, context: ProcessingContext, threshold: float = 27.0) -> ProcessingContext:
        """
        Orchestrates scene detection within a processing pipeline context.
        
        Args:
            context: The ProcessingContext aggregate root.
            threshold: Sensitivity for the detection algorithm.
            
        Returns:
            The mutated ProcessingContext with updated scenes.
            
        Raises:
            SceneDetectionException: If detection fails or unrecoverable error occurs.
        """
        video = context.video
        logical_path = video.logical_path
        
        logger.info(f"Initiating scene detection for {logical_path} with threshold {threshold}")
        
        # 1. Resolve path securely
        try:
            absolute_path = self._storage._provider._resolve_and_validate_path(logical_path)
        except Exception as e:
            logger.error(f"Failed to resolve path for scene detection: {str(e)}")
            raise SceneDetectionException(f"Invalid logical path: {str(e)}")

        if not absolute_path.exists():
            raise SceneDetectionException(f"Video file not found at logical path: {logical_path}")
            
        # 2. Extract Duration
        duration = video.metadata.duration_seconds if video.metadata else None

        # 3. Detect Scenes
        try:
            raw_scenes = await self._detector.detect_scenes(str(absolute_path), threshold)
            logger.debug(f"Detector returned {len(raw_scenes)} raw scenes.")
        except MetadataExtractionError as e:
            raise SceneDetectionException(f"Underlying detector failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during scene detection: {str(e)}")
            raise SceneDetectionException(f"Scene detection failed due to an internal error.")

        # 4. Validate and Normalize
        valid_scenes = self._validate_and_normalize(raw_scenes, duration)
        
        # 5. Handle Empty Results
        if not valid_scenes:
            logger.warning(f"No valid scenes detected for {logical_path}. Creating fallback scene.")
            fallback_duration = duration if duration and duration > 0 else 0.0
            valid_scenes = [Scene(seconds_start=0.0, seconds_end=fallback_duration)]
            
        # 6. Update Context
        context.video.scenes = valid_scenes
        context.current_stage_name = "SceneDetection"
        logger.info(f"Scene detection complete for {logical_path}. Valid scenes: {len(valid_scenes)}")
        
        return context

    def _validate_and_normalize(self, scenes: List[Scene], max_duration: float = None) -> List[Scene]:
        """
        Normalizes timestamps to 3 decimal places and strips invalid boundaries.
        """
        valid = []
        for s in scenes:
            # Normalize precision
            start = round(max(0.0, s.seconds_start), 3)
            end = round(s.seconds_end, 3)
            
            # Cap at duration if known
            if max_duration is not None and max_duration > 0:
                end = min(end, round(max_duration, 3))
                
            # Drop logically invalid scenes
            if end <= start:
                continue
                
            s.seconds_start = start
            s.seconds_end = end
            valid.append(s)
            
        return valid

