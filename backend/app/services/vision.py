"""
Vision Analysis Application Service.
Orchestrates the semantic interpretation of visual payloads.
"""
from loguru import logger

from app.domain.interfaces.vision import VisionAnalyzer
from app.domain.models.analysis import VisionInputPackage
from app.domain.models.vision import (
    VisionAnalysisRequest,
    VisionAnalysisResult
)
from app.services.prompt_builder import PromptBuilder
from app.core.exceptions import ValidationException, VisionAnalysisException


class VisionAnalysisService:
    """
    Coordinates the communication between the domain and the Vision AI provider.
    Strictly isolated from Video Processing Contexts, ensuring it operates purely
    on AI-ready payloads.
    """
    
    def __init__(self, analyzer: VisionAnalyzer, prompt_builder: PromptBuilder):
        self._analyzer = analyzer
        self._prompt_builder = prompt_builder

    async def process(self, package: VisionInputPackage) -> VisionAnalysisResult:
        """
        Submits a VisionInputPackage to the Vision AI provider for analysis.
        
        Args:
            package: The standardized package containing compressed images and metadata.
            
        Returns:
            The structured semantic understanding of the scene.
            
        Raises:
            ValidationException: If the package is invalid (e.g., zero images).
            VisionAnalysisException: If the underlying provider fails.
        """
        if not package.key_frames:
            raise ValidationException(f"Cannot analyze VisionInputPackage for scene {package.scene.scene_id}: No keyframes present.")
            
        logger.info(f"Initiating Vision Analysis for scene {package.scene.scene_id} ({len(package.key_frames)} keyframes).")
        
        # Ask PromptBuilder to compile the images and metadata into a standardized request
        request = self._prompt_builder.build_scene_analysis_prompt(package)
        
        try:
            result = await self._analyzer.analyze(request)
            
            logger.info(f"Vision Analysis successful for scene {package.scene.scene_id}.")
            return result
            
        except Exception as e:
            logger.error(f"Vision Analysis failed for scene {package.scene.scene_id}: {str(e)}")
            raise VisionAnalysisException(f"Failed to analyze scene {package.scene.scene_id}: {str(e)}")
