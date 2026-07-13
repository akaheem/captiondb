import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.infrastructure.scene.pyscenedetect import PySceneDetectDetector
from app.domain.models.video import Scene
from app.core.exceptions import MetadataExtractionError


class MockFrameTimecode:
    def __init__(self, seconds: float):
        self.seconds = seconds
        
    def get_seconds(self) -> float:
        return self.seconds


@pytest.mark.asyncio
async def test_detect_scenes_success(tmp_path):
    """Test successful scene detection mapping perfectly to Domain Models."""
    detector = PySceneDetectDetector()
    
    dummy_video = tmp_path / "test_video.mp4"
    dummy_video.write_bytes(b"dummy")
    
    # Mock PySceneDetect's detect function
    mock_scenes = [
        (MockFrameTimecode(0.0), MockFrameTimecode(5.5)),
        (MockFrameTimecode(5.5), MockFrameTimecode(12.0))
    ]
    
    with patch("app.infrastructure.scene.pyscenedetect.detect", return_value=mock_scenes) as mock_detect:
        scenes = await detector.detect_scenes(str(dummy_video))
        
        assert len(scenes) == 2
        assert scenes[0].seconds_start == 0.0
        assert scenes[0].seconds_end == 5.5
        
        assert scenes[1].seconds_start == 5.5
        assert scenes[1].seconds_end == 12.0
        
        # Verify it passed the right path
        mock_detect.assert_called_once()


@pytest.mark.asyncio
async def test_detect_scenes_file_not_found():
    """Test handling of non-existent files."""
    detector = PySceneDetectDetector()
    
    with pytest.raises(MetadataExtractionError) as exc_info:
        await detector.detect_scenes("/path/that/does/not/exist.mp4")
        
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_detect_scenes_library_failure(tmp_path):
    """Test exception mapping when PySceneDetect/OpenCV crashes."""
    detector = PySceneDetectDetector()
    
    dummy_video = tmp_path / "corrupt_video.mp4"
    dummy_video.write_bytes(b"dummy")
    
    with patch("app.infrastructure.scene.pyscenedetect.detect", side_effect=ValueError("OpenCV failed to open stream")):
        with pytest.raises(MetadataExtractionError) as exc_info:
            await detector.detect_scenes(str(dummy_video))
            
        assert "Failed to detect scenes: OpenCV failed to open stream" in str(exc_info.value)
