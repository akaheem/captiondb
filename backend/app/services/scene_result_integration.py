"""
Scene Result Integration Service.
Merges the outputs of the AI Pipeline back into the core Domain Models.
"""
from typing import Dict
from loguru import logger

from app.domain.models.analysis import ProcessingContext
from app.domain.models.pipeline import VideoPipelineResult, ScenePipelineResult
from app.domain.models.integration import (
    VideoIntegrationResult,
    SceneIntegrationResult,
    IntegrationStatistics,
    CostBreakdown,
    IntegrationStatus
)


class SceneResultIntegrationService:
    """
    Integrates AI analysis results into the original Video aggregate.
    Maintains ordering, isolates failures, and aggregates final statistics and costs.
    """
    
    # Rough estimate weights per token for cost calculation (micro-cents)
    # This represents a hypothetical cost mapping
    VISION_PROMPT_COST_WEIGHT = 0.001
    VISION_COMP_COST_WEIGHT = 0.003
    CAPTION_PROMPT_COST_WEIGHT = 0.0005
    CAPTION_COMP_COST_WEIGHT = 0.0015
    
    def process(self, context: ProcessingContext, pipeline_result: VideoPipelineResult) -> VideoIntegrationResult:
        """
        Merges pipeline results into the video aggregate.
        
        Args:
            context: The original processing context containing the video.
            pipeline_result: The results from the AI Pipeline.
            
        Returns:
            A VideoIntegrationResult with the fully enriched video.
        """
        video = context.video
        logger.info(f"Starting Scene Result Integration for video {video.id}")
        
        integration_result = VideoIntegrationResult(
            video_id=video.id,
            status=IntegrationStatus.FAILED,
            enriched_video=video
        )
        
        if not pipeline_result.scene_results:
            logger.warning(f"No scene results provided for video {video.id}.")
            integration_result.status = IntegrationStatus.SUCCESS
            return integration_result
            
        # Map original scenes by id to ensure we preserve exact ordering and don't lose anything
        scene_map = {s.scene_id: s for s in video.scenes}
        
        for ai_scene in pipeline_result.scene_results:
            integration_result.statistics.total_scenes += 1
            
            if ai_scene.scene_id not in scene_map:
                logger.error(f"AI Pipeline returned unknown scene ID: {ai_scene.scene_id}")
                integration_result.statistics.failed_scenes += 1
                integration_result.scene_results.append(
                    SceneIntegrationResult(
                        scene_id=ai_scene.scene_id,
                        is_success=False,
                        enriched_scene=None, # type: ignore
                        error_message="Scene ID not found in original video"
                    )
                )
                continue
                
            scene = scene_map[ai_scene.scene_id]
            
            if not ai_scene.is_success:
                logger.warning(f"Integrating failed scene {ai_scene.scene_id}: {ai_scene.error_message}")
                integration_result.statistics.failed_scenes += 1
                integration_result.scene_results.append(
                    SceneIntegrationResult(
                        scene_id=ai_scene.scene_id,
                        is_success=False,
                        enriched_scene=scene,
                        error_message=ai_scene.error_message
                    )
                )
                continue
                
            try:
                self._enrich_scene(scene, ai_scene, integration_result.statistics, integration_result.cost)
                integration_result.statistics.successful_scenes += 1
                
                integration_result.scene_results.append(
                    SceneIntegrationResult(
                        scene_id=ai_scene.scene_id,
                        is_success=True,
                        enriched_scene=scene
                    )
                )
            except Exception as e:
                logger.error(f"Failed to enrich scene {ai_scene.scene_id}: {str(e)}")
                integration_result.statistics.failed_scenes += 1
                integration_result.scene_results.append(
                    SceneIntegrationResult(
                        scene_id=ai_scene.scene_id,
                        is_success=False,
                        enriched_scene=scene,
                        error_message=str(e)
                    )
                )
                
        # Calculate averages
        if integration_result.statistics.total_scenes > 0:
            integration_result.statistics.average_scene_latency_seconds = (
                integration_result.statistics.total_overall_latency_seconds / integration_result.statistics.total_scenes
            )
            
        # Determine final status
        if integration_result.statistics.failed_scenes == 0:
            integration_result.status = IntegrationStatus.SUCCESS
        elif integration_result.statistics.successful_scenes > 0:
            integration_result.status = IntegrationStatus.PARTIAL_SUCCESS
        else:
            integration_result.status = IntegrationStatus.FAILED
            integration_result.error_message = "Failed to integrate any scenes."
            
        logger.info(
            f"Integration complete for {video.id}. Status: {integration_result.status.value}, "
            f"Success: {integration_result.statistics.successful_scenes}, "
            f"Failed: {integration_result.statistics.failed_scenes}, "
            f"Est. Cost: {integration_result.cost.estimated_total_cost:.4f}"
        )
        return integration_result
        
    def _enrich_scene(
        self, 
        scene, 
        ai_scene: ScenePipelineResult, 
        stats: IntegrationStatistics,
        cost: CostBreakdown
    ):
        """Mutates the scene object with AI metadata while strictly avoiding overwriting unrelated fields."""
        
        # 1. Integrate Vision Data
        if ai_scene.vision_result:
            vr = ai_scene.vision_result
            scene.summary = vr.scene_summary
            scene.objects = vr.objects.copy()
            scene.activities = vr.activities.copy()
            scene.colors = vr.dominant_colors.copy()
            
            # OCR placeholder if present (schema agnostic)
            if hasattr(vr, 'ocr_text') and vr.ocr_text:
                scene.ocr_text = vr.ocr_text
                
            # Aggregate Vision Tokens and Latency (Placeholder for latency since we didn't track granular vision latency yet)
            # But we can track tokens
            if hasattr(vr, 'metadata') and hasattr(vr.metadata, 'usage'):
                usage = vr.metadata.usage
                stats.total_prompt_tokens += usage.prompt_tokens
                stats.total_completion_tokens += usage.completion_tokens
                
                v_cost = (usage.prompt_tokens * self.VISION_PROMPT_COST_WEIGHT) + (usage.completion_tokens * self.VISION_COMP_COST_WEIGHT)
                cost.estimated_vision_cost += v_cost
                cost.estimated_total_cost += v_cost
                
        # 2. Integrate Caption Data
        if ai_scene.caption_result and ai_scene.caption_result.candidates:
            # We pick the first candidate as the primary caption for the requested tone
            best_candidate = ai_scene.caption_result.candidates[0]
            scene.captions[ai_scene.target_tone] = best_candidate.text
            
            # Aggregate Caption Tokens
            cr = ai_scene.caption_result
            if hasattr(cr, 'metadata') and hasattr(cr.metadata, 'usage'):
                usage = cr.metadata.usage
                stats.total_prompt_tokens += usage.prompt_tokens
                stats.total_completion_tokens += usage.completion_tokens
                
                c_cost = (usage.prompt_tokens * self.CAPTION_PROMPT_COST_WEIGHT) + (usage.completion_tokens * self.CAPTION_COMP_COST_WEIGHT)
                cost.estimated_caption_cost += c_cost
                cost.estimated_total_cost += c_cost
                
        # 3. Attach standard AI Metadata block
        scene.ai_metadata["integrated"] = True
        scene.ai_metadata["target_tone"] = ai_scene.target_tone.value
        if ai_scene.vision_result and hasattr(ai_scene.vision_result, 'safety_flags'):
            scene.ai_metadata["safety_flags"] = ai_scene.vision_result.safety_flags
            
        # 4. Aggregate latencies
        stats.total_overall_latency_seconds += ai_scene.processing_time_seconds
