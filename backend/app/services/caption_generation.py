"""
Caption Generation Application Service.
Orchestrates the conversion of Vision Analysis Results into human-readable captions.
"""
from typing import List
from loguru import logger

from app.domain.models.video import CaptionTone
from app.domain.models.vision import VisionAnalysisResult
from app.domain.models.caption import CaptionGenerationResult, CaptionCandidate
from app.domain.interfaces.caption import CaptionGenerator
from app.services.prompt_builder import PromptBuilder
from app.core.exceptions import ValidationException


class CaptionGenerationService:
    """
    Coordinates the communication between the domain and the Caption Generation AI provider.
    Ensures structural integrity of both inputs and outputs.
    """
    
    def __init__(self, generator: CaptionGenerator, prompt_builder: PromptBuilder):
        self._generator = generator
        self._prompt_builder = prompt_builder

    async def process(self, analysis_result: VisionAnalysisResult, target_tone: CaptionTone) -> CaptionGenerationResult:
        """
        Generates captions for a specific scene based on its visual analysis.
        
        Args:
            analysis_result: The structured semantic output from the Vision Analyzer.
            target_tone: The desired tone for the caption.
            
        Returns:
            A structured CaptionGenerationResult containing validated caption candidates.
            
        Raises:
            ValidationException: If input analysis is empty, or if generated captions are invalid.
            Exception: If the underlying provider fails.
        """
        if not isinstance(target_tone, CaptionTone):
            raise ValidationException(f"Invalid target tone provided: {target_tone}")
            
        self._validate_analysis(analysis_result)
        
        # Build prompt using centralized logic
        request = self._prompt_builder.build_caption_generation_prompt(analysis_result, target_tone)
        
        logger.info(f"Initiating Caption Generation for tone: {target_tone.value}")
        
        try:
            result = await self._generator.generate(request)
        except Exception as e:
            logger.error(f"Caption generation failed: {str(e)}")
            raise e
            
        # Post-generation validation
        self._validate_captions(result.candidates)
        
        logger.info(f"Successfully generated {len(result.candidates)} captions.")
        return result
        
    def _validate_analysis(self, result: VisionAnalysisResult) -> None:
        if not result.scene_summary or not result.scene_summary.strip():
            raise ValidationException("Cannot generate caption: scene summary is empty.")
            
        if not result.objects:
            raise ValidationException("Cannot generate caption: no objects detected in scene.")
            
    def _validate_captions(self, candidates: List[CaptionCandidate]) -> None:
        if not candidates:
            raise ValidationException("Provider returned zero caption candidates.")
            
        seen_texts = set()
        for candidate in candidates:
            text = candidate.text.strip()
            
            if not text:
                raise ValidationException("Provider returned an empty caption.")
                
            if len(text) > 1000:
                raise ValidationException(f"Caption exceeds maximum length: {len(text)} characters.")
                
            if text in seen_texts:
                raise ValidationException("Provider returned duplicate captions.")
            seen_texts.add(text)
