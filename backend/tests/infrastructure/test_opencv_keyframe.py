import pytest
import cv2
import numpy as np
import base64

from app.infrastructure.keyframe.opencv import OpenCVFrameQualityAnalyzer, OpenCVKeyframeSelector
from app.domain.models.ai import AIImageContent


def create_base64_image(color: int, noise: bool = False) -> str:
    """Helper to generate a valid base64 JPEG data URI for testing."""
    img = np.full((100, 100, 3), color, dtype=np.uint8)
    if noise:
        # Add random noise to increase info/blur score
        noise_matrix = np.random.randint(0, 50, (100, 100, 3), dtype=np.uint8)
        img = cv2.add(img, noise_matrix)
        
    _, buffer = cv2.imencode('.jpg', img)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_str}"


@pytest.fixture
def analyzer():
    return OpenCVFrameQualityAnalyzer()


@pytest.fixture
def selector(analyzer):
    return OpenCVKeyframeSelector(analyzer)


@pytest.mark.asyncio
async def test_low_information_dropped(analyzer, selector):
    # Solid black frame (very low stddev)
    black_img = AIImageContent(data_uri=create_base64_image(0))
    
    score = await analyzer.analyze(black_img)
    assert score.information_score < 2.0
    assert not score.is_valid
    
    # Selector should drop it entirely
    selected = await selector.select_keyframes([black_img])
    assert len(selected) == 0


@pytest.mark.asyncio
async def test_duplicate_filtering(analyzer, selector):
    # Two identical noisy frames
    np.random.seed(42) # Ensure identical noise
    img1 = AIImageContent(data_uri=create_base64_image(128, noise=True))
    
    np.random.seed(42)
    img2 = AIImageContent(data_uri=create_base64_image(128, noise=True))
    
    # One different noisy frame
    np.random.seed(100)
    img3 = AIImageContent(data_uri=create_base64_image(128, noise=True))
    
    selected = await selector.select_keyframes([img1, img2, img3])
    
    # Should drop the duplicate (img2) and keep img1 and img3
    assert len(selected) == 2


@pytest.mark.asyncio
async def test_corrupted_image(analyzer, selector):
    corrupted = AIImageContent(data_uri="data:image/jpeg;base64,invalid_base64_data!!!")
    
    # Analyzer should raise KeyframeSelectionError
    with pytest.raises(Exception):
        await analyzer.analyze(corrupted)
        
    # Selector should swallow it, warn, and return 0 frames
    selected = await selector.select_keyframes([corrupted])
    assert len(selected) == 0
