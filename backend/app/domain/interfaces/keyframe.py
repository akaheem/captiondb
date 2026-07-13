"""
Keyframe Selection Interfaces.
Defines boundaries for frame quality analysis and ranking.
"""
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

from app.domain.models.ai import AIImageContent


@dataclass
class QualityScore:
    """
    Represents the objective quality metrics of a single frame.
    Higher final_score implies a better candidate for Vision AI.
    """
    blur_score: float         # Higher is sharper
    information_score: float  # Higher means more contrast/detail
    final_score: float        # Combined weighted score
    image_hash: str           # Perceptual hash for duplicate detection
    is_valid: bool = True     # False if image is corrupted or too low quality


class FrameQualityAnalyzer(ABC):
    """
    Analyzes an image to compute objective quality metrics.
    """
    
    @abstractmethod
    async def analyze(self, image: AIImageContent) -> QualityScore:
        """
        Calculates blur, information, and perceptual hash for a frame.
        
        Args:
            image: The extracted candidate frame.
            
        Returns:
            A QualityScore object.
        """
        pass


class KeyframeSelector(ABC):
    """
    Evaluates and ranks a list of candidate frames, filtering out duplicates
    and selecting the highest quality frames.
    """
    
    @abstractmethod
    async def select_keyframes(self, candidates: List[AIImageContent]) -> List[AIImageContent]:
        """
        Filters and ranks candidates.
        
        Args:
            candidates: All frames extracted for a scene.
            
        Returns:
            The highest quality frames, with near-duplicates and blurry frames removed.
        """
        pass
