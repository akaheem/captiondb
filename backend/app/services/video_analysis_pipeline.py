"""
Video Analysis Pipeline.
Orchestrates the complete Video Analysis Subsystem (Phases 4.1 to 4.5).
"""
from typing import List, Optional
from loguru import logger
import traceback

from app.domain.models.analysis import ProcessingContext, VideoAnalysisPipelineResult
from app.services.scene import SceneDetectionService
from app.services.frame import FrameSamplingService
from app.services.keyframe import KeyframeSelectionService
from app.services.vision_preparation import VisionInputPreparationService
from app.core.exceptions import (
    SceneDetectionError,
    FrameExtractionError,
    KeyframeSelectionError,
    ImagePreparationException,
    VideoAnalysisPipelineException
)


class VideoAnalysisPipeline:
    """
    The main orchestrator for the Video Analysis Subsystem.
    Executes the sequential phases to transform a raw video into Vision AI payloads.
    """
    
    def __init__(
        self,
        scene_service: SceneDetectionService,
        frame_service: FrameSamplingService,
        keyframe_service: KeyframeSelectionService,
        vision_prep_service: VisionInputPreparationService
    ):
        self._scene_service = scene_service
        self._frame_service = frame_service
        self._keyframe_service = keyframe_service
        self._vision_prep_service = vision_prep_service

    async def run(self, context: ProcessingContext) -> VideoAnalysisPipelineResult:
        """
        Executes the pipeline in sequential order.
        
        Flow:
        1. Scene Detection
        2. Frame Sampling
        3. Keyframe Selection
        4. Vision Input Preparation
        
        Args:
            context: The initialized aggregate root containing the Video.
            
        Returns:
            VideoAnalysisPipelineResult indicating success or failure, with prepared packages.
        """
        video_id = context.video.id
        logical_path = context.video.logical_path
        logger.info(f"Starting Video Analysis Pipeline for video {video_id} ({logical_path})")
        
        try:
            # 1. Scene Detection
            logger.debug(f"Pipeline Stage 1: Scene Detection ({video_id})")
            context = await self._scene_service.process(context)
            
            # 2. Frame Sampling
            logger.debug(f"Pipeline Stage 2: Frame Sampling ({video_id})")
            context = await self._frame_service.process(context)
            
            # 3. Keyframe Selection
            logger.debug(f"Pipeline Stage 3: Keyframe Selection ({video_id})")
            context = await self._keyframe_service.process(context)
            
            # 4. Vision Input Preparation
            logger.debug(f"Pipeline Stage 4: Vision Input Preparation ({video_id})")
            packages = await self._vision_prep_service.process(context)
            
            logger.info(f"Video Analysis Pipeline completed successfully for {video_id}. Generated {len(packages)} packages.")
            
            return VideoAnalysisPipelineResult(
                is_success=True,
                packages=packages,
                failed_scene_ids=[], # Partial failure handling at scene level is delegated to individual services.
                error_message=None
            )
            
        except (
            SceneDetectionError,
            FrameExtractionError,
            KeyframeSelectionError,
            ImagePreparationException
        ) as expected_err:
            # Domain-specific errors.
            error_msg = f"Pipeline failed at {context.current_stage_name}: {str(expected_err)}"
            logger.error(error_msg)
            return VideoAnalysisPipelineResult(
                is_success=False,
                error_message=error_msg
            )
            
        except Exception as unexpected_err:
            # Unhandled infrastructure or system errors
            error_msg = f"Critical Pipeline Failure at {context.current_stage_name}: {str(unexpected_err)}"
            logger.exception(error_msg)
            # Raise a specific pipeline exception for critical system faults
            raise VideoAnalysisPipelineException(error_msg)
