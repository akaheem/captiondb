"""
Scene Detection Interface.
Defines the boundary for scene detection infrastructure.
"""
from abc import ABC, abstractmethod
from typing import List

from app.domain.models.video import Scene

class SceneDetector(ABC):
    """
    Abstract interface for detecting scenes in a video.
    
    Purpose: Isolates the Application layer from specific computer vision libraries (e.g., PySceneDetect, OpenCV).
    Expected Inputs: An absolute path to a local video file, and an optional threshold.
    Expected Outputs: A list of Scene Domain models.
    """
    
    @abstractmethod
    async def detect_scenes(self, absolute_path: str, threshold: float = 27.0) -> List[Scene]:
        """
        Analyzes a video file and returns its temporal scene boundaries.
        
        Args:
            absolute_path: The absolute path on the host filesystem where the video resides.
            threshold: The sensitivity of the scene detection (algorithm-specific).
            
        Returns:
            A list of Scene objects with seconds_start and seconds_end populated.
            
        Raises:
            MetadataExtractionError: If the file cannot be processed or the library fails.
        """
        pass
