"""
FFprobe Metadata Extractor Implementation.
Infrastructure layer adapter for extracting video metadata via the ffprobe subprocess.
"""
import asyncio
import json
from typing import Optional
from loguru import logger

from app.domain.models.video import VideoMetadata, VideoDimensions, VideoFormat
from app.domain.interfaces.metadata import MetadataExtractor
from app.core.exceptions import MetadataExtractionError


class FFprobeMetadataExtractor(MetadataExtractor):
    """
    Concrete implementation of MetadataExtractor using asyncio and ffprobe.
    """
    def __init__(self, timeout_seconds: int = 15):
        self._timeout = timeout_seconds

    async def extract(self, absolute_file_path: str) -> Optional[VideoMetadata]:
        """
        Executes ffprobe as a non-blocking subprocess to extract video metadata.
        """
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            absolute_file_path
        ]
        
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for execution with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self._timeout
            )
            
            if process.returncode != 0:
                logger.error(f"FFprobe failed with return code {process.returncode}")
                # We do not leak stderr directly to the caller, we map it.
                raise MetadataExtractionError("Video file is corrupt or format is unsupported.")

            # Parse JSON
            try:
                data = json.loads(stdout.decode("utf-8"))
            except json.JSONDecodeError:
                logger.error("FFprobe returned malformed JSON.")
                raise MetadataExtractionError("Failed to parse metadata from video.")
                
            return self._map_to_domain(data, absolute_file_path)

        except asyncio.TimeoutError:
            logger.error(f"FFprobe execution timed out after {self._timeout}s for {absolute_file_path}")
            # Try to kill the process to avoid zombie processes
            try:
                process.kill()
            except Exception:
                pass
            raise MetadataExtractionError("Metadata extraction timed out.")
            
        except FileNotFoundError:
            logger.critical("ffprobe executable not found on the system.")
            raise MetadataExtractionError("System configuration error: Metadata extractor unavailable.")
            
        except MetadataExtractionError:
            # Re-raise already mapped domain exceptions
            raise
            
        except Exception as e:
            # Catch-all for unexpected OS errors
            logger.error(f"Unexpected error executing ffprobe: {str(e)}")
            raise MetadataExtractionError("An unexpected error occurred during extraction.")

    def _map_to_domain(self, data: dict, path: str) -> VideoMetadata:
        """
        Safely maps the raw JSON output to the Domain VideoMetadata object.
        """
        # Find the video stream
        video_stream = next(
            (stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"), 
            None
        )
        
        if not video_stream:
            raise MetadataExtractionError("No video stream found in the file.")

        form = data.get("format", {})
        
        # Safely extract size
        size_bytes = int(form.get("size", 0))
        
        # Safely extract duration
        duration_str = form.get("duration") or video_stream.get("duration")
        duration_seconds = float(duration_str) if duration_str else 0.0
        
        # Safely extract FPS (r_frame_rate is usually like "30000/1001")
        fps = 0.0
        fps_str = video_stream.get("r_frame_rate", "0/0")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            if den and int(den) > 0:
                fps = float(num) / float(den)
                
        codec = video_stream.get("codec_name", "unknown")
        
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        
        dimensions = VideoDimensions(width=width, height=height)
        resolution = f"{width}x{height}"
        
        # Determine format based on format_name (e.g., "mov,mp4,m4a,3gp,3g2,mj2")
        format_names = form.get("format_name", "").lower()
        video_format = VideoFormat.UNKNOWN
        if "mp4" in format_names:
            video_format = VideoFormat.MP4
        elif "mov" in format_names:
            video_format = VideoFormat.MOV
        elif "webm" in format_names:
            video_format = VideoFormat.WEBM
        elif "avi" in format_names:
            video_format = VideoFormat.AVI

        return VideoMetadata(
            size_bytes=size_bytes,
            duration_seconds=round(duration_seconds, 2),
            fps=round(fps, 2),
            codec=codec,
            resolution=resolution,
            dimensions=dimensions,
            format=video_format
        )
