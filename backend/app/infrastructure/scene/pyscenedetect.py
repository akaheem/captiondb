"""
PySceneDetect Infrastructure Adapter.
Implements the SceneDetector interface using the scenedetect library.
"""
import asyncio
from typing import List
from pathlib import Path
from loguru import logger

from scenedetect import detect, ContentDetector

from app.domain.interfaces.scene import SceneDetector
from app.domain.models.video import Scene
from app.core.exceptions import MetadataExtractionError


class PySceneDetectDetector(SceneDetector):
    """
    Concrete implementation of SceneDetector using PySceneDetect.
    Runs CPU-bound computer vision tasks in a thread pool to avoid blocking FastAPI.
    """
    
    def _run_detection(self, absolute_path: str, threshold: float) -> List[Scene]:
        """
        Synchronous detection wrapper.
        """
        path = Path(absolute_path)
        if not path.exists():
            raise MetadataExtractionError(f"Video file not found at {absolute_path}")
            
        try:
            logger.debug(f"Starting PySceneDetect on {absolute_path} with threshold {threshold}")
            
            # Using the simplified scenedetect.detect API
            # detect() returns a list of tuples: (FrameTimecode, FrameTimecode)
            scene_list = detect(
                video_path=str(path),
                detector=ContentDetector(threshold=threshold)
            )
            
            scenes = []
            for start_time, end_time in scene_list:
                scenes.append(
                    Scene(
                        seconds_start=start_time.get_seconds(),
                        seconds_end=end_time.get_seconds()
                    )
                )
                
            logger.info(f"PySceneDetect found {len(scenes)} scenes in {path.name}")
            return scenes
            
        except Exception as e:
            logger.error(f"PySceneDetect failure on {absolute_path}: {str(e)}")
            raise MetadataExtractionError(f"Failed to detect scenes: {str(e)}")

    async def detect_scenes(self, absolute_path: str, threshold: float = 27.0) -> List[Scene]:
        """
        Asynchronously delegates the detection to a background thread.
        """
        return await asyncio.to_thread(self._run_detection, absolute_path, threshold)
