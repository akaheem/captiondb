"""
Keyframe Selection Service.
Orchestrates the selection of high-quality frames from raw candidates.
"""
from typing import Dict, List
from loguru import logger

from app.domain.interfaces.keyframe import KeyframeSelector
from app.domain.models.analysis import ProcessingContext
from app.domain.models.ai import AIImageContent
from app.core.exceptions import ValidationException, KeyframeSelectionError


class KeyframeSelectionService:
    """
    Coordinates the filtering and ranking of extracted candidate frames.
    Produces the final set of images that will be sent to the Vision API.
    """
    
    def __init__(self, keyframe_selector: KeyframeSelector):
        self._selector = keyframe_selector

    async def process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Iterates over all extracted candidates in the context and filters them.
        
        Args:
            context: The ProcessingContext containing extracted_frames.
            
        Returns:
            The mutated context where extracted_frames only contains selected keyframes.
        """
        video = context.video
        logical_path = video.logical_path
        
        if not context.extracted_frames:
            raise ValidationException(f"Cannot select keyframes for {logical_path}. No candidate frames exist in context.")
            
        logger.info(f"Initiating keyframe selection for {logical_path}. Evaluating candidates across {len(context.extracted_frames)} scenes.")
        
        final_keyframes_map: Dict[str, List[AIImageContent]] = {}
        total_candidates = 0
        total_selected = 0
        
        for scene_id, candidates in context.extracted_frames.items():
            candidate_count = len(candidates)
            total_candidates += candidate_count
            
            if candidate_count == 0:
                logger.warning(f"Scene {scene_id} has 0 candidates. Skipping.")
                final_keyframes_map[scene_id] = []
                continue
                
            try:
                selected = await self._selector.select_keyframes(candidates)
                final_keyframes_map[scene_id] = selected
                total_selected += len(selected)
                logger.debug(f"Scene {scene_id}: {candidate_count} candidates -> {len(selected)} selected.")
                
            except Exception as e:
                logger.error(f"Failed to select keyframes for scene {scene_id}: {str(e)}")
                raise KeyframeSelectionError(f"Selection failed: {str(e)}")
                
        # Update Context
        context.extracted_frames = final_keyframes_map
        context.current_stage_name = "KeyframeSelection"
        
        logger.info(
            f"Keyframe selection complete for {logical_path}. "
            f"Reduced {total_candidates} candidates to {total_selected} high-quality keyframes."
        )
        return context
