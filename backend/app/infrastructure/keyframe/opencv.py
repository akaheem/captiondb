"""
OpenCV Keyframe Infrastructure.
Implements quality analysis and duplicate detection using lightweight cv2 operations.
"""
import cv2
import numpy as np
import base64
import asyncio
from typing import List, Tuple
from loguru import logger

from app.domain.interfaces.keyframe import FrameQualityAnalyzer, KeyframeSelector, QualityScore
from app.domain.models.ai import AIImageContent
from app.core.exceptions import KeyframeSelectionError


class OpenCVFrameQualityAnalyzer(FrameQualityAnalyzer):
    """
    Analyzes images for blur, low information, and computes perceptual hashes.
    """
    
    def _decode_base64(self, data_uri: str) -> np.ndarray:
        """Decodes the Data URI back into an OpenCV image buffer."""
        try:
            # Strip the 'data:image/jpeg;base64,' prefix
            header, encoded = data_uri.split(",", 1)
            img_data = base64.b64decode(encoded)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("cv2.imdecode returned None")
            return img
        except Exception as e:
            raise KeyframeSelectionError(f"Failed to decode image: {str(e)}")

    def _dhash(self, image: np.ndarray, hash_size: int = 8) -> str:
        """
        Computes the Difference Hash (dHash) of an image.
        Resizes to (hash_size + 1, hash_size) -> Grayscale -> compares adjacent pixels.
        """
        resized = cv2.resize(image, (hash_size + 1, hash_size))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Compare adjacent pixels (True if left > right)
        diff = gray[:, 1:] > gray[:, :-1]
        
        # Convert the boolean array to a hexadecimal string
        return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

    def _run_analysis(self, image_content: AIImageContent) -> QualityScore:
        """Synchronous workload for CPU bound analysis."""
        img = self._decode_base64(image_content.data_uri)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Blur Score (Variance of Laplacian)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 2. Information Score (Pixel Standard Deviation)
        _, stddev = cv2.meanStdDev(gray)
        info_score = float(stddev[0][0])
        
        # 3. Perceptual Hash
        image_hash = str(self._dhash(img))
        
        # 4. Final Score 
        # Weighting Strategy: 
        # Sharpness is important, but a perfectly sharp image of a blank wall is useless.
        # We heavily weight the information score (contrast/details) combined with a baseline blur score.
        final_score = (blur_score * 0.4) + (info_score * 0.6)
        
        # Mark as invalid if completely blank (e.g., solid black frame)
        is_valid = info_score >= 2.0
        
        return QualityScore(
            blur_score=float(blur_score),
            information_score=info_score,
            final_score=float(final_score),
            image_hash=image_hash,
            is_valid=is_valid
        )

    async def analyze(self, image: AIImageContent) -> QualityScore:
        return await asyncio.to_thread(self._run_analysis, image)


class OpenCVKeyframeSelector(KeyframeSelector):
    """
    Selects keyframes by rejecting duplicates and ranking by QualityScore.
    """
    def __init__(self, analyzer: FrameQualityAnalyzer):
        self._analyzer = analyzer
        # Threshold for Hamming Distance (Number of differing bits)
        # 0 = identical. <= 10 means very similar.
        self.duplicate_threshold = 5

    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculates hamming distance between two integer hashes stored as strings."""
        try:
            h1 = int(hash1)
            h2 = int(hash2)
            # Count set bits in the XOR
            return bin(h1 ^ h2).count('1')
        except ValueError:
            return 64 # Fallback to completely different

    async def select_keyframes(self, candidates: List[AIImageContent]) -> List[AIImageContent]:
        if not candidates:
            return []
            
        # 1. Analyze all candidates
        scored_candidates: List[Tuple[AIImageContent, QualityScore]] = []
        for c in candidates:
            try:
                score = await self._analyzer.analyze(c)
                if score.is_valid:
                    scored_candidates.append((c, score))
            except KeyframeSelectionError as e:
                logger.warning(f"Dropping candidate frame due to analysis failure: {e}")
                
        if not scored_candidates:
            return []
            
        # 2. Sort by highest final_score first
        scored_candidates.sort(key=lambda item: item[1].final_score, reverse=True)
        
        # 3. Filter Duplicates
        selected: List[AIImageContent] = []
        accepted_hashes: List[str] = []
        
        for frame, score in scored_candidates:
            is_duplicate = False
            for accepted_hash in accepted_hashes:
                distance = self._hamming_distance(score.image_hash, accepted_hash)
                if distance <= self.duplicate_threshold:
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                selected.append(frame)
                accepted_hashes.append(score.image_hash)
                
        # If all frames were duplicates of each other (e.g. static shot), 
        # the highest quality one was appended first and the rest rejected.
        logger.debug(f"Selector filtered {len(candidates)} candidates down to {len(selected)} high-quality keyframes.")
        return selected
