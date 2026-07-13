"""
Frame Sampling Service.
Application service that implements the Adaptive Scene-Length Aware Sampling strategy.
"""
from typing import List, Dict
from loguru import logger
import math

from app.domain.interfaces.frame import FrameExtractor
from app.domain.models.video import Scene
from app.domain.models.analysis import ProcessingContext
from app.domain.models.ai import AIImageContent
from app.services.storage import StorageService
from app.core.exceptions import ValidationException, FrameExtractionError


class FrameSamplingService:
    """
    Coordinates the extraction of representative candidate frames from scenes.
    Uses an adaptive sampling strategy to prevent overwhelming downstream Vision AI models.
    """
    
    def __init__(self, frame_extractor: FrameExtractor, storage_service: StorageService):
        """Injected dependencies."""
        self._extractor = frame_extractor
        self._storage = storage_service

        # Adaptive Strategy Configuration
        self.min_frames = 1
        self.max_frames = 10
        self.target_fps = 0.5  # 1 frame every 2 seconds

    def _calculate_timestamps(self, scene: Scene) -> List[float]:
        """
        Calculates evenly distributed timestamps across a scene's duration.
        Sampling occurs in the middle of each calculated chunk to avoid boundary transitions.
        """
        start = scene.seconds_start
        end = scene.seconds_end
        duration = end - start
        
        # Edge case: invalid or zero duration
        if duration <= 0:
            return [start]
            
        # Adaptive calculation
        target_frames = math.floor(duration * self.target_fps)
        target_frames = max(self.min_frames, min(self.max_frames, target_frames))
        
        interval = duration / target_frames
        
        timestamps = []
        for i in range(target_frames):
            # Sample from the middle of the interval chunk
            ts = start + (interval / 2.0) + (i * interval)
            timestamps.append(round(ts, 3))
            
        return timestamps

    async def process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Orchestrates frame sampling for all validated scenes in the processing context.
        
        Args:
            context: The ProcessingContext aggregate root containing validated scenes.
            
        Returns:
            The mutated ProcessingContext with extracted AIImageContent.
            
        Raises:
            ValidationException: If no scenes exist.
            FrameExtractionError: If the underlying extractor fails.
        """
        video = context.video
        logical_path = video.logical_path
        scenes = video.scenes
        
        if not scenes:
            raise ValidationException(f"Cannot sample frames for {logical_path}. No scenes defined in context.")
            
        logger.info(f"Initiating adaptive frame sampling for {logical_path}. ({len(scenes)} scenes)")
        
        # 1. Resolve path securely
        try:
            absolute_path = self._storage._provider._resolve_and_validate_path(logical_path)
        except Exception as e:
            raise ValidationException(f"Invalid logical path for sampling: {str(e)}")

        if not absolute_path.exists():
            raise FrameExtractionError(f"Video file not found at logical path: {logical_path}")
            
        # 2. Iterate scenes and extract
        extracted_frames_map: Dict[str, List[AIImageContent]] = {}
        total_frames = 0
        
        for scene in scenes:
            timestamps = self._calculate_timestamps(scene)
            logger.debug(f"Scene {scene.scene_id} ({scene.seconds_end - scene.seconds_start:.2f}s) -> Requesting {len(timestamps)} frames.")
            
            try:
                # Extract frames for the current scene
                frames = await self._extractor.extract_frames(str(absolute_path), timestamps)
                
                # If extraction returned fewer frames than requested, we log but continue
                if len(frames) != len(timestamps):
                    logger.warning(f"Scene {scene.scene_id}: Requested {len(timestamps)} frames, but extracted {len(frames)}.")
                    
                extracted_frames_map[scene.scene_id] = frames
                total_frames += len(frames)
                
            except FrameExtractionError as e:
                # We escalate the domain error immediately to halt processing
                raise e
            except Exception as e:
                logger.error(f"Unexpected failure extracting frames for scene {scene.scene_id}: {str(e)}")
                raise FrameExtractionError(f"Internal sampling failure: {str(e)}")
                
        # 3. Update Context
        context.extracted_frames.update(extracted_frames_map)
        context.current_stage_name = "FrameSampling"
        
        logger.info(f"Frame sampling complete for {logical_path}. Total extracted: {total_frames} frames.")
        return context
