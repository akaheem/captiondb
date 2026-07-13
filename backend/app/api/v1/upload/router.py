"""
API Router for Uploading Videos.
Handles the HTTP boundary and delegates to UploadService.
"""
from typing import AsyncIterator
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException

from app.api.schemas.upload import UploadResponse, VideoMetadataSchema, VideoDimensionsSchema
from app.dependencies.services import get_upload_service
from app.services.upload import UploadService

router = APIRouter()


async def chunk_generator(file: UploadFile, chunk_size: int = 1024 * 1024 * 5) -> AsyncIterator[bytes]:
    """
    Reads the FastAPI UploadFile in chunks asynchronously.
    Prevents loading the entire file into memory (OOM mitigation).
    """
    while chunk := await file.read(chunk_size):
        yield chunk


@router.post(
    "/",
    response_model=UploadResponse,
    summary="Upload a new video for captioning.",
    description=(
        "Accepts a multipart form upload containing the video file and target project name. "
        "The file is streamed directly to storage to prevent memory exhaustion, validated against "
        "domain rules, and processed by FFprobe to extract intrinsic metadata."
    )
)
async def upload_video(
    project_name: str = Form(..., description="The ID or Name of the project to associate this video with."),
    file: UploadFile = File(..., description="The video file payload (e.g. video/mp4)."),
    upload_service: UploadService = Depends(get_upload_service)
) -> UploadResponse:
    """
    Thin controller delegating to UploadService.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing in upload.")
        
    # Convert FastAPI's UploadFile into an abstracted AsyncIterator[bytes] stream
    stream = chunk_generator(file)
    
    # Delegate to Application Layer
    result = await upload_service.process_upload(
        project_name=project_name,
        original_filename=file.filename,
        content=stream
    )
    
    if not result.success or not result.video:
        # We rely on the global exception handlers for deep domain exceptions, but for
        # validation failures returned gracefully by the service, we map them here.
        raise HTTPException(status_code=400, detail={"errors": result.errors})
        
    # Map the Domain Model back to the API Schema
    metadata_schema = None
    if result.video.metadata:
        metadata_schema = VideoMetadataSchema(
            size_bytes=result.video.metadata.size_bytes,
            duration_seconds=result.video.metadata.duration_seconds,
            fps=result.video.metadata.fps,
            codec=result.video.metadata.codec,
            resolution=result.video.metadata.resolution,
            dimensions=VideoDimensionsSchema(
                width=result.video.metadata.dimensions.width,
                height=result.video.metadata.dimensions.height
            ),
            format=result.video.metadata.format
        )
        
    return UploadResponse(
        success=True,
        video_id=result.video.id,
        project_name=result.video.project_name,
        status=result.video.state.status,
        metadata=metadata_schema,
        errors=result.errors
    )
