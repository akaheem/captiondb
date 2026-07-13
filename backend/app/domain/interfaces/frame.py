"""
Frame Extraction Interface.
Defines the boundary for extracting image frames from a video at specific timestamps.
"""
from abc import ABC, abstractmethod
from typing import List

from app.domain.models.ai import AIImageContent


class FrameExtractor(ABC):
    """
    Abstract interface for extracting frames from a video file.
    
    Purpose: Isolates the Application layer from specific media libraries (OpenCV, FFmpeg).
    Expected Inputs: An absolute path to a local video file, and a list of timestamps (in seconds).
    Expected Outputs: A list of AIImageContent (holding base64 encoded JPEGs) corresponding to the requested timestamps.
    """
    
    @abstractmethod
    async def extract_frames(self, absolute_path: str, timestamps: List[float]) -> List[AIImageContent]:
        """
        Extracts frames from the video at the given timestamps.
        
        Args:
            absolute_path: The absolute path on the host filesystem where the video resides.
            timestamps: A list of floats representing seconds from the start of the video.
            
        Returns:
            A list of AIImageContent objects. The length matches the length of timestamps.
            
        Raises:
            FrameExtractionError: If the file cannot be processed or a frame cannot be read.
        """
        pass
