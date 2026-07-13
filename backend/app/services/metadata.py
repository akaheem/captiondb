"""
Metadata Extraction Service.

Orchestrates the metadata extraction process.
Strictly separated from the underlying parsing binaries (FFprobe/OpenCV).
"""
from typing import Optional
from loguru import logger

from app.core.config import Settings
from app.domain.models.video import VideoMetadata
from app.domain.interfaces.metadata import MetadataExtractor


class MetadataExtractionService:
    """
    Application service that coordinates the extraction of video properties.
    It does not contain parsing logic; it delegates entirely to the MetadataExtractor.
    """
    
    def __init__(self, extractor: MetadataExtractor, settings: Settings):
        self._extractor = extractor
        self._settings = settings

    async def get_metadata(self, absolute_file_path: str) -> Optional[VideoMetadata]:
        """
        Coordinates the extraction workflow.
        Returns the populated VideoMetadata domain value object, or None if extraction fails.
        """
        try:
            metadata = await self._extractor.extract(absolute_file_path)
            
            if not metadata:
                logger.warning(f"Extractor failed to resolve metadata for: {absolute_file_path}")
                return None
                
            logger.info(f"Extracted metadata: {metadata.resolution} @ {metadata.fps}fps, {metadata.duration_seconds}s")
            return metadata
            
        except Exception as e:
            # We catch broad exceptions here to prevent the orchestration layer
            # from crashing if the underlying infrastructure adapter fails unexpectedly.
            logger.error(f"Metadata extraction coordination failed for {absolute_file_path}: {str(e)}")
            return None
