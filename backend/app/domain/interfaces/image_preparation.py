"""
Image Preparation Interface.
Contract for standardizing image resolutions and payloads for Vision AI consumption.
"""
from abc import ABC, abstractmethod
from typing import List

from app.domain.models.ai import AIImageContent


class ImagePreprocessor(ABC):
    """
    Abstract interface for preprocessing selected keyframes.
    
    Responsibilities:
    - JPEG compression
    - Resolution normalization (e.g., resizing to max dimensions)
    - Payload size validation (ensuring base64 strings don't exceed API limits)
    - Re-encoding and MIME type assertion
    """
    
    @abstractmethod
    async def preprocess_images(self, images: List[AIImageContent]) -> List[AIImageContent]:
        """
        Prepares a batch of images for Vision AI consumption.
        
        Args:
            images: The selected, raw candidate keyframes.
            
        Returns:
            A new list of AIImageContent with standardized payloads and optimized sizes.
            
        Raises:
            ImagePreparationException: If compression fails or final payload is too large.
        """
        pass
