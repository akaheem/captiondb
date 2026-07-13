import asyncio
import json
import pytest
from unittest.mock import patch, AsyncMock

from app.infrastructure.metadata.ffprobe import FFprobeMetadataExtractor, MetadataExtractionError
from app.domain.models.video import VideoFormat

# Sample successful ffprobe output
VALID_FFPROBE_OUTPUT = {
    "streams": [
        {
            "codec_type": "audio"
        },
        {
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "r_frame_rate": "30000/1001",
            "duration": "120.5"
        }
    ],
    "format": {
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "size": "15000000",
        "duration": "120.5"
    }
}

@pytest.fixture
def extractor():
    return FFprobeMetadataExtractor(timeout_seconds=2)


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_extract_success(mock_create_subprocess_exec, extractor):
    """Test successful metadata extraction."""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (json.dumps(VALID_FFPROBE_OUTPUT).encode(), b"")
    mock_process.returncode = 0
    mock_create_subprocess_exec.return_value = mock_process

    metadata = await extractor.extract("/path/to/video.mp4")

    assert metadata is not None
    assert metadata.dimensions.width == 1920
    assert metadata.dimensions.height == 1080
    assert metadata.codec == "h264"
    assert metadata.size_bytes == 15000000
    assert metadata.duration_seconds == 120.5
    assert metadata.fps == 29.97
    assert metadata.format == VideoFormat.MP4


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_extract_invalid_json(mock_create_subprocess_exec, extractor):
    """Test handling of malformed JSON from ffprobe."""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"Invalid JSON output", b"")
    mock_process.returncode = 0
    mock_create_subprocess_exec.return_value = mock_process

    with pytest.raises(MetadataExtractionError, match="Failed to parse metadata"):
        await extractor.extract("/path/to/corrupt.mp4")


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_extract_missing_executable(mock_create_subprocess_exec, extractor):
    """Test handling of missing ffprobe executable."""
    mock_create_subprocess_exec.side_effect = FileNotFoundError()

    with pytest.raises(MetadataExtractionError, match="System configuration error"):
        await extractor.extract("/path/to/video.mp4")


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_extract_timeout(mock_create_subprocess_exec, extractor):
    """Test handling of ffprobe timeouts."""
    mock_process = AsyncMock()
    mock_process.communicate.side_effect = asyncio.TimeoutError()
    mock_create_subprocess_exec.return_value = mock_process

    with pytest.raises(MetadataExtractionError, match="Metadata extraction timed out"):
        await extractor.extract("/path/to/slow.mp4")


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_extract_nonzero_return_code(mock_create_subprocess_exec, extractor):
    """Test handling of ffprobe failing (e.g. corrupt file)."""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"Invalid data found when processing input")
    mock_process.returncode = 1
    mock_create_subprocess_exec.return_value = mock_process

    with pytest.raises(MetadataExtractionError, match="corrupt or format is unsupported"):
        await extractor.extract("/path/to/bad.mp4")


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_extract_no_video_stream(mock_create_subprocess_exec, extractor):
    """Test handling of files with audio but no video stream."""
    mock_process = AsyncMock()
    output = {"streams": [{"codec_type": "audio"}], "format": {}}
    mock_process.communicate.return_value = (json.dumps(output).encode(), b"")
    mock_process.returncode = 0
    mock_create_subprocess_exec.return_value = mock_process

    with pytest.raises(MetadataExtractionError, match="No video stream found"):
        await extractor.extract("/path/to/audio.mp3")
