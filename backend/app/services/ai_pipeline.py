"""
AI Pipeline Orchestrator.
Coordinates the end-to-end execution of Video Analysis, Vision AI, and Caption Generation.
"""
import time
from typing import List, Optional
from loguru import logger
from datetime import datetime, timezone

from app.domain.models.analysis import ProcessingContext
from app.domain.models.pipeline import (
    VideoPipelineResult,
    ScenePipelineResult,
    PipelineStatus,
    PipelineStatistics,
    PipelineUsage
)
from app.services.video_analysis_pipeline import VideoAnalysisPipeline
from app.services.vision import VisionAnalysisService
from app.services.caption_generation import CaptionGenerationService
from app.services.scene_result_integration import SceneResultIntegrationService
from app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from app.domain.models.video import VideoStatus
from app.core.exceptions import VideoAnalysisPipelineException


class AIPipelineService:
    """
    Orchestrates the entire AI processing workflow for a video.
    Executes the Video Analysis Pipeline to extract scenes/frames, then loops
    through each scene to perform Vision Analysis and Caption Generation.
    """
    
    def __init__(
        self,
        video_pipeline: VideoAnalysisPipeline,
        vision_service: VisionAnalysisService,
        caption_service: CaptionGenerationService,
        scene_integration_service: SceneResultIntegrationService,
        unit_of_work: AbstractUnitOfWork
    ):
        self._video_pipeline = video_pipeline
        self._vision_service = vision_service
        self._caption_service = caption_service
        self._integration_service = scene_integration_service
        self._uow = unit_of_work

    async def process(self, context: ProcessingContext) -> VideoPipelineResult:
        """
        Executes the AI Pipeline for the given context.
        
        Args:
            context: The ProcessingContext initialized with a video and target tone.
            
        Returns:
            The fully aggregated VideoPipelineResult containing success rates, usages, and outputs.
        """
        video_id = context.video.id
        logger.info(f"Starting AI Pipeline for video {video_id}")
        
        result = VideoPipelineResult(video_id=video_id, status=PipelineStatus.FAILED)
        
        # Step 0: Ensure we have the latest Video aggregate from the database
        # and mark it as actively processing.
        try:
            async with self._uow:
                db_video = await self._uow.videos.get_by_id(video_id)
                if not db_video:
                    raise ValueError(f"Video {video_id} not found in database.")
                db_video.state.status = VideoStatus.PROCESSING
                db_video.state.started_at = datetime.now(timezone.utc)
                db_video.state.error_message = None
                await self._uow.videos.update(db_video)
                await self._uow.commit()
                context.video = db_video
        except Exception as e:
            logger.error(f"Failed to load video {video_id} for AI Pipeline: {str(e)}")
            result.error_message = f"Database load failed: {str(e)}"
            result.completed_at = datetime.now(timezone.utc)
            return result
        
        # Step 1: Execute Video Analysis to get VisionInputPackages
        try:
            video_analysis_result = await self._video_pipeline.run(context)
        except Exception as e:
            logger.exception(f"Video Analysis Pipeline failed critically for {video_id}: {str(e)}")
            result.error_message = f"Video Analysis Pipeline failed: {str(e)}"
            result.completed_at = datetime.now(timezone.utc)
            await self._persist_video_status(context, VideoStatus.FAILED, result.error_message)
            return result

        if not video_analysis_result.is_success:
            logger.error(f"Video Analysis Pipeline failed cleanly for {video_id}: {video_analysis_result.error_message}")
            result.error_message = video_analysis_result.error_message
            result.completed_at = datetime.now(timezone.utc)
            await self._persist_video_status(context, VideoStatus.FAILED, result.error_message)
            return result

        packages = video_analysis_result.packages
        result.statistics.total_scenes = len(packages)

        if not packages:
            logger.warning(f"No scenes detected for video {video_id}. Pipeline completing empty.")
            result.status = PipelineStatus.SUCCESS
            result.completed_at = datetime.now(timezone.utc)
            await self._persist_video_status(context, VideoStatus.COMPLETED, None)
            return result
            
        logger.info(f"Video {video_id} analysis complete. Proceeding to process {len(packages)} scenes.")
        
        # Step 2 & 3: Process each package through Vision and Caption Generation.
        # Future optimization: Process sequentially here but architecturally allows asyncio.gather()
        
        for package in packages:
            scene_id = package.scene.scene_id
            target_tone = package.target_tone
            scene_start = time.time()
            
            scene_result = ScenePipelineResult(
                scene_id=scene_id,
                target_tone=target_tone,
                is_success=False
            )
            
            try:
                # 2. Vision Analysis
                vision_result = await self._vision_service.process(package)
                scene_result.vision_result = vision_result
                
                # Aggregate vision tokens if supported
                if hasattr(vision_result, "metadata") and hasattr(vision_result.metadata, "usage"):
                    usage = vision_result.metadata.usage
                    result.usage.add(usage.prompt_tokens, usage.completion_tokens, usage.total_tokens)
                
                # 3. Caption Generation
                caption_result = await self._caption_service.process(vision_result, target_tone)
                scene_result.caption_result = caption_result
                
                # Aggregate caption tokens
                if hasattr(caption_result, "metadata") and hasattr(caption_result.metadata, "usage"):
                    usage = caption_result.metadata.usage
                    result.usage.add(usage.prompt_tokens, usage.completion_tokens, usage.total_tokens)
                    
                scene_result.is_success = True
                result.statistics.successful_scenes += 1
                logger.debug(f"Scene {scene_id} processed successfully.")
                
            except Exception as e:
                scene_result.error_message = str(e)
                result.statistics.failed_scenes += 1
                logger.error(f"Scene {scene_id} failed during AI processing: {str(e)}")
                # We do NOT raise here to ensure partial processing completes.
                
            scene_result.processing_time_seconds = time.time() - scene_start
            result.statistics.total_processing_time_seconds += scene_result.processing_time_seconds
            
            result.scene_results.append(scene_result)
            
        # Step 4: Aggregate final status
        result.completed_at = datetime.now(timezone.utc)
        
        if result.statistics.failed_scenes == 0:
            result.status = PipelineStatus.SUCCESS
        elif result.statistics.successful_scenes > 0:
            result.status = PipelineStatus.PARTIAL_SUCCESS
        else:
            result.status = PipelineStatus.FAILED
            # Surface the first scene's actual error — "all scenes failed" alone
            # makes provider misconfiguration (bad key, wrong model) undiagnosable.
            first_error = next(
                (sr.error_message for sr in result.scene_results if sr.error_message),
                None
            )
            result.error_message = (
                f"All scenes failed processing. First error: {first_error}"
                if first_error else "All scenes failed processing."
            )
            
        logger.info(f"AI Pipeline completed for {video_id}. Status: {result.status.value}, "
                    f"Success: {result.statistics.successful_scenes}, Failed: {result.statistics.failed_scenes}")
                    
        # Step 5: Integrate results into the Video aggregate and persist
        try:
            integration_result = self._integration_service.process(context, result)

            enriched = integration_result.enriched_video
            if result.status in (PipelineStatus.SUCCESS, PipelineStatus.PARTIAL_SUCCESS):
                enriched.state.status = VideoStatus.COMPLETED
                enriched.state.error_message = result.error_message
            else:
                enriched.state.status = VideoStatus.FAILED
                enriched.state.error_message = result.error_message or "All scenes failed processing."
            enriched.state.completed_at = datetime.now(timezone.utc)
            enriched.state.progress_percent = 100.0

            async with self._uow:
                await self._uow.videos.update(enriched)
                await self._uow.commit()

            logger.info(f"Successfully persisted AI enrichment for video {video_id}")
        except Exception as e:
            logger.error(f"Failed to integrate and persist AI results for video {video_id}: {str(e)}")
            # We don't overwrite the pipeline result, but we log the failure.

        return result

    async def _persist_video_status(
        self,
        context: ProcessingContext,
        status: VideoStatus,
        error_message: Optional[str]
    ) -> None:
        """Persists a terminal lifecycle status so videos never stay stuck in PROCESSING."""
        try:
            video = context.video
            video.state.status = status
            video.state.error_message = error_message
            video.state.completed_at = datetime.now(timezone.utc)
            async with self._uow:
                await self._uow.videos.update(video)
                await self._uow.commit()
        except Exception as e:
            logger.error(f"Failed to persist status {status.value} for video {context.video.id}: {str(e)}")
