"""
OpenCV Frame Extractor Infrastructure Adapter.
Implements FrameExtractor using opencv-python-headless.
"""
import asyncio
import cv2
import base64
from typing import List
from loguru import logger
from pathlib import Path

from app.domain.interfaces.frame import FrameExtractor
from app.domain.models.ai import AIImageContent
from app.core.exceptions import FrameExtractionError


class OpenCVFrameExtractor(FrameExtractor):
    """
    Concrete implementation of FrameExtractor using OpenCV.
    Runs strictly in a background thread to prevent blocking FastAPI's event loop.
    Reads frames dynamically using random-access seeking.
    """
    
    def _run_extraction(self, absolute_path: str, timestamps: List[float]) -> List[AIImageContent]:
        path = Path(absolute_path)
        if not path.exists():
            raise FrameExtractionError(f"Video file not found at {absolute_path}")
            
        logger.debug(f"Starting frame extraction for {absolute_path}, {len(timestamps)} frames.")
        
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise FrameExtractionError(f"OpenCV failed to open video file {absolute_path}")
            
        results: List[AIImageContent] = []
        
        try:
            for ts in timestamps:
                # Seek to exact timestamp in milliseconds
                cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)
                
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Could not read frame at {ts}s for {absolute_path}. Using fallback strategy or skipping.")
                    continue
                    
                # Encode frame to JPEG
                # We enforce a standard quality compression (85%) to prevent memory blowups when sent to AI.
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                success, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                if not success:
                    raise FrameExtractionError(f"Failed to encode frame at {ts}s to JPEG.")
                    
                # Convert to base64 Data URI
                b64_str = base64.b64encode(buffer).decode('utf-8')
                data_uri = f"data:image/jpeg;base64,{b64_str}"
                
                results.append(AIImageContent(data_uri=data_uri))
                
        except Exception as e:
            logger.error(f"Error during OpenCV frame extraction: {str(e)}")
            raise FrameExtractionError(f"Extraction failed: {str(e)}")
        finally:
            cap.release()
            
        logger.info(f"Extracted {len(results)} frames from {path.name}")
        return results

    async def extract_frames(self, absolute_path: str, timestamps: List[float]) -> List[AIImageContent]:
        """
        Delegates the CPU-bound OpenCV read operations to a background thread.
        """
        # Short-circuit if no timestamps requested
        if not timestamps:
            return []
            
        return await asyncio.to_thread(self._run_extraction, absolute_path, timestamps)
