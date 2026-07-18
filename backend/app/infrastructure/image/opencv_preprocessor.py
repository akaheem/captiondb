"""
OpenCV Image Preprocessor.

Implements ImagePreprocessor using OpenCV: decodes base64 JPEG data URIs,
normalizes resolution to Vision-AI-friendly dimensions, re-compresses, and
enforces payload size limits. Runs in a background thread to keep FastAPI's
event loop responsive.
"""
import asyncio
import base64
from typing import List

import cv2
import numpy as np
from loguru import logger

from app.core.exceptions import ImagePreparationException
from app.domain.interfaces.image_preparation import ImagePreprocessor
from app.domain.models.ai import AIImageContent


class OpenCVImagePreprocessor(ImagePreprocessor):
    """
    Concrete preprocessor for Vision AI keyframes.

    - Downscales frames whose longest edge exceeds ``max_dimension``.
    - Re-encodes to JPEG at ``jpeg_quality``.
    - Rejects frames whose final base64 payload exceeds ``max_payload_bytes``.
    """

    DATA_URI_PREFIX = "data:image/jpeg;base64,"

    def __init__(
        self,
        max_dimension: int = 1024,
        jpeg_quality: int = 80,
        max_payload_bytes: int = 4 * 1024 * 1024,  # 4 MB per image, well under API limits
    ):
        self._max_dimension = max_dimension
        self._jpeg_quality = jpeg_quality
        self._max_payload_bytes = max_payload_bytes

    def _process_one(self, image: AIImageContent) -> AIImageContent:
        data_uri = image.data_uri
        if "," not in data_uri:
            raise ImagePreparationException("Image content is not a valid data URI.")

        b64_payload = data_uri.split(",", 1)[1]
        try:
            raw = base64.b64decode(b64_payload)
        except (ValueError, TypeError) as e:
            raise ImagePreparationException(f"Failed to decode base64 image payload: {str(e)}")

        frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise ImagePreparationException("OpenCV failed to decode image bytes.")

        # Resolution normalization: cap the longest edge, preserve aspect ratio
        height, width = frame.shape[:2]
        longest = max(height, width)
        if longest > self._max_dimension:
            scale = self._max_dimension / longest
            frame = cv2.resize(
                frame,
                (max(1, int(width * scale)), max(1, int(height * scale))),
                interpolation=cv2.INTER_AREA,
            )

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self._jpeg_quality]
        success, buffer = cv2.imencode(".jpg", frame, encode_param)
        if not success:
            raise ImagePreparationException("Failed to re-encode image to JPEG.")

        b64_str = base64.b64encode(buffer).decode("utf-8")
        if len(b64_str) > self._max_payload_bytes:
            raise ImagePreparationException(
                f"Image payload ({len(b64_str)} bytes base64) exceeds the {self._max_payload_bytes} byte limit."
            )

        return AIImageContent(data_uri=f"{self.DATA_URI_PREFIX}{b64_str}")

    def _process_batch(self, images: List[AIImageContent]) -> List[AIImageContent]:
        return [self._process_one(img) for img in images]

    async def preprocess_images(self, images: List[AIImageContent]) -> List[AIImageContent]:
        """
        Prepares a batch of images for Vision AI consumption.

        Raises:
            ImagePreparationException: If decoding/compression fails or a final payload is too large.
        """
        if not images:
            return []

        logger.debug(f"Preprocessing {len(images)} keyframes (max_dim={self._max_dimension}, quality={self._jpeg_quality}).")
        try:
            # CPU-bound OpenCV work runs off the event loop
            return await asyncio.to_thread(self._process_batch, images)
        except ImagePreparationException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during image preprocessing: {str(e)}")
            raise ImagePreparationException(f"Image preprocessing failed: {str(e)}")
