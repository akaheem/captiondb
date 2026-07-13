"""
Metadata Extractor Interface.

Abstracts the physical inspection of video files from the Application layer.
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models.video import VideoMetadata


class MetadataExtractor(ABC):
    """
    Abstract interface for extracting intrinsic properties from video files.
    
    Purpose: Decouples business logic from specific extraction binaries (e.g., FFmpeg, MediaInfo).
    Responsibilities: Read a physical video file and return a fully populated domain model.
    Expected Inputs: An absolute path to a file currently residing on the host machine.
    Expected Outputs: A standard VideoMetadata object or None on critical failure.
    Failure Behavior: Should catch sub-process errors and raise standard domain exceptions.
    Extension Points: Can be implemented via FFprobeAdapter, OpenCVAdapter, or MediaInfoAdapter.
    """
    
    @abstractmethod
    async def extract(self, absolute_file_path: str) -> Optional[VideoMetadata]:
        """Extracts metadata from the provided host file path."""
        pass
