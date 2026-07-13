"""
Vision Input Preparation Service.
Orchestrates the packaging of selected keyframes into provider-agnostic VisionInputPackages.
"""
from typing import List, Dict
from loguru import logger

from app.domain.interfaces.image_preparation import ImagePreprocessor
from app.domain.models.analysis import ProcessingContext, VisionInputPackage
from app.domain.models.video import CaptionTone
from app.core.exceptions import ValidationException, ImagePreparationException


class VisionInputPreparationService:
    """
    Coordinates the preprocessing of keyframes and generation of Vision AI payloads.
    Provides complete insulation between the video extraction phases and the AI inference phases.
    """
    
    def __init__(self, image_preprocessor: ImagePreprocessor):
        self._preprocessor = image_preprocessor

    def _determine_target_tone(self, context: ProcessingContext) -> CaptionTone:
        """Extracts the target tone from runtime metadata, defaulting to NONE."""
        tone_str = context.runtime_metadata.get("target_tone", CaptionTone.NONE.value)
        try:
            return CaptionTone(tone_str)
        except ValueError:
            return CaptionTone.NONE

    async def process(self, context: ProcessingContext) -> List[VisionInputPackage]:
        """
        Transforms the extracted and selected keyframes into standardized VisionInputPackages.
        
        Args:
            context: The ProcessingContext containing extracted_frames.
            
        Returns:
            A list of VisionInputPackage objects, one per scene.
            
        Raises:
            ValidationException: If no scenes or frames are present.
            ImagePreparationException: If the preprocessor fails.
        """
        video = context.video
        logical_path = video.logical_path
        
        if not video.scenes:
            raise ValidationException(f"Cannot prepare vision input for {logical_path}: No scenes exist.")
            
        if not context.extracted_frames:
            raise ValidationException(f"Cannot prepare vision input for {logical_path}: No keyframes exist.")
            
        logger.info(f"Initiating Vision Input Preparation for {logical_path}.")
        
        target_tone = self._determine_target_tone(context)
        packages: List[VisionInputPackage] = []
        
        for i, scene in enumerate(video.scenes):
            raw_keyframes = context.extracted_frames.get(scene.scene_id, [])
            
            if not raw_keyframes:
                logger.warning(f"Scene {scene.scene_id} has no keyframes. Skipping Vision package creation.")
                continue
                
            try:
                # Delegate compression, resizing, and base64 normalization to infrastructure
                processed_frames = await self._preprocessor.preprocess_images(raw_keyframes)
            except Exception as e:
                logger.error(f"Image preprocessing failed for scene {scene.scene_id}: {str(e)}")
                raise ImagePreparationException(f"Failed to prepare images for scene {scene.scene_id}: {str(e)}")
                
            # Create the provider-agnostic package
            package = VisionInputPackage(
                video_id=video.id,
                scene=scene,
                video_context=video.metadata,
                target_tone=target_tone,
                key_frames=processed_frames,
                previous_scene_context=None, # Context injection can be populated later by the pipeline
                next_scene_context=None
            )
            
            packages.append(package)
            
        # Update Context State
        context.current_stage_name = "VisionInputPreparation"
        
        logger.info(f"Vision Input Preparation complete. Generated {len(packages)} packages.")
        return packages
